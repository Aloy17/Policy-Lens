#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_ROOT="$REPO_ROOT/dist"
OUTPUT_DIR="$OUTPUT_ROOT/PolicyLens"
if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "Build this distribution on an Apple Silicon Mac (arm64)." >&2; exit 1
fi
if [[ ! -f "$REPO_ROOT/data/manifest.csv" || ! -d "$REPO_ROOT/data/pdfs" ]]; then
  echo "Missing data/manifest.csv or data/pdfs." >&2; exit 1
fi
if [[ -e "$OUTPUT_DIR" ]]; then
  echo "Output already exists: $OUTPUT_DIR" >&2
  echo "Move it aside before rebuilding. This script will not delete it." >&2
  exit 1
fi
mkdir -p "$OUTPUT_ROOT"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/policylens-build.XXXXXX")"
trap 'rm -rf "$BUILD_DIR"' EXIT
APP="$OUTPUT_DIR/PolicyLens.app"
RES="$APP/Contents/Resources"
CODE="$RES/app"
RUNTIME="$RES/runtime"
DATA="$OUTPUT_DIR/PolicyLens Data"
mkdir -p "$CODE" "$DATA/corpus/pdfs" "$DATA/models" "$DATA/logs"
echo "[1/6] Fetching temporary micromamba..."
curl -Ls https://micro.mamba.pm/api/micromamba/osx-arm64/latest | tar -xvj -C "$BUILD_DIR" bin/micromamba
MAMBA="$BUILD_DIR/bin/micromamba"
export MAMBA_ROOT_PREFIX="$BUILD_DIR/mamba-root"
echo "[2/6] Creating the ARM64 runtime..."
"$MAMBA" create -y -p "$BUILD_DIR/env" -f "$SCRIPT_DIR/environment.yml"
"$MAMBA" run -p "$BUILD_DIR/env" conda-pack -p "$BUILD_DIR/env" -o "$BUILD_DIR/runtime.tar.gz"
mkdir -p "$RUNTIME"
tar -xzf "$BUILD_DIR/runtime.tar.gz" -C "$RUNTIME"
"$RUNTIME/bin/conda-unpack"
echo "[3/6] Copying application and corpus..."
for item in src ui ingest.py search.py config.yaml; do cp -R "$REPO_ROOT/$item" "$CODE/"; done
cp "$REPO_ROOT/data/manifest.csv" "$DATA/corpus/manifest.csv"
cp -R "$REPO_ROOT/data/pdfs/." "$DATA/corpus/pdfs/"
echo "[4/6] Downloading and validating the embedding model..."
export POLICYLENS_MODEL_PATH="$DATA/models/multi-qa-MiniLM-L6-cos-v1"
"$RUNTIME/bin/python" - <<'PY'
import os
from pathlib import Path
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
target = Path(os.environ["POLICYLENS_MODEL_PATH"])
target.mkdir(parents=True, exist_ok=True)
snapshot_download("sentence-transformers/multi-qa-MiniLM-L6-cos-v1", local_dir=str(target))
SentenceTransformer(str(target), local_files_only=True)
PY
echo "[5/6] Creating the app launcher..."
mkdir -p "$APP/Contents/MacOS"
cat > "$APP/Contents/MacOS/PolicyLens" <<'LAUNCHER'
#!/bin/bash
set -euo pipefail
APP="$(cd "$(dirname "$0")/../.." && pwd)"
ROOT="$(cd "$APP/.." && pwd)"
RES="$APP/Contents/Resources"
RUNTIME="$RES/runtime"
CODE="$RES/app"
DATA="$ROOT/PolicyLens Data"
export POLICYLENS_APP_DIR="$CODE"
export POLICYLENS_DATA_DIR="$DATA"
export POLICYLENS_MODEL_PATH="$DATA/models/multi-qa-MiniLM-L6-cos-v1"
export POLICYLENS_MANIFEST_PATH="$DATA/corpus/manifest.csv"
export POLICYLENS_TESSERACT_CMD="$RUNTIME/bin/tesseract"
export PATH="$RUNTIME/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="$DATA/home"
export XDG_CACHE_HOME="$DATA/cache"
export HF_HOME="$DATA/cache/huggingface"
export TORCH_HOME="$DATA/cache/torch"
export STREAMLIT_CONFIG_DIR="$DATA/config/streamlit"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONNOUSERSITE=1
mkdir -p "$HOME" "$XDG_CACHE_HOME" "$HF_HOME" "$TORCH_HOME" "$STREAMLIT_CONFIG_DIR" "$DATA/logs"
TESSDATA="$(find "$RUNTIME" -name eng.traineddata -print -quit)"
if [[ -z "$TESSDATA" ]]; then
  osascript -e 'display alert "PolicyLens OCR data missing" message "Rebuild the application bundle."' || true
  exit 1
fi
export TESSDATA_PREFIX="$(dirname "$TESSDATA")"
if [[ ! -f "$DATA/.index-ready" ]]; then
  "$RUNTIME/bin/python" "$CODE/ingest.py" --input "$DATA/corpus/pdfs" --manifest "$DATA/corpus/manifest.csv" --collection policylens_v1
  "$RUNTIME/bin/python" - <<'PY'
import chromadb
from pathlib import Path
database = Path(__import__("os").environ["POLICYLENS_DATA_DIR"]) / "chroma_db"
client = chromadb.PersistentClient(path=str(database))
for name in ("policylens_v1_fixed", "policylens_v1_structure"):
    collection = client.get_collection(name)
    if collection.count() == 0:
        raise SystemExit(f"Index validation failed: {name} is empty")
PY
  touch "$DATA/.index-ready"
fi
exec "$RUNTIME/bin/python" -m streamlit run "$CODE/ui/app.py" --server.headless=false --server.port=8501 --browser.gatherUsageStats=false
LAUNCHER
chmod +x "$APP/Contents/MacOS/PolicyLens"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>PolicyLens</string>
<key>CFBundleIdentifier</key><string>com.aloy17.policylens</string>
<key>CFBundleName</key><string>PolicyLens</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>13.0</string>
</dict></plist>
PLIST
echo "[6/6] Checking bundle..."
test -x "$RUNTIME/bin/python"
test -x "$RUNTIME/bin/tesseract"
test -f "$DATA/models/multi-qa-MiniLM-L6-cos-v1/config.json"
cat > "$OUTPUT_ROOT/README.txt" <<'NOTES'
Keep PolicyLens.app and PolicyLens Data together.
Open PolicyLens.app to start. First launch indexes the bundled PDF corpus.
To remove all application-managed files, quit the app and delete the complete
PolicyLens distribution folder. Deleting only the .app leaves PolicyLens Data.
macOS may retain generic system metadata outside this folder.
This local build is unsigned; Gatekeeper approval may be required.
Public distribution requires Developer ID signing and notarization.
NOTES
echo "Build prepared at $OUTPUT_DIR"
