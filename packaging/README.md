# Standalone macOS build (Apple Silicon)

Run this on an Apple Silicon Mac with internet access:

```bash
bash packaging/build_macos.sh
```

The build creates `dist/PolicyLens/` with `PolicyLens.app` and an adjacent
`PolicyLens Data/` folder. The app bundle contains a packed conda-forge ARM64
Python environment, application dependencies and Tesseract OCR. The data folder
contains the corpus, local embedding model, ChromaDB index, logs and caches.
No Homebrew, Python, or Tesseract installation is made system-wide.

Open `dist/PolicyLens/PolicyLens.app`. The first launch indexes the bundled
PDF corpus before starting the local Streamlit interface. The build must run
on Apple Silicon; it is not a universal Intel/ARM app. The result is unsigned
and intended for local use. Developer ID signing and notarization are required
for a public release.

Keep the app and data folder together. To remove application-managed files,
quit PolicyLens and delete the complete `dist/PolicyLens/` folder. Deleting
only the .app leaves the adjacent data folder. macOS may retain generic system
metadata outside the folder.

The build script refuses to overwrite an existing output. Move the old output
yourself after checking it, then run the build again.
