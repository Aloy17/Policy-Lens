import os
import sys
from pathlib import Path

import streamlit as st
import yaml

ROOT = Path(os.environ.get(
    "POLICYLENS_APP_DIR",
    Path(__file__).resolve().parent.parent,
)).expanduser().resolve()
sys.path.insert(0, str(ROOT))

from src.runtime_paths import APP_ROOT, app_path, data_path
from src.embedder import Embedder
from src.vector_store import VectorStore

st.set_page_config(page_title="PolicyLens | Regulatory Search", page_icon="⚖️",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }
.hero { padding: 1.8rem; border: 1px solid rgba(128,128,128,0.25); border-radius: 14px; margin-bottom: 1.5rem; }
.hero h1 { margin: 0; font-size: 2.3rem; font-weight: 700; }
.hero p { margin-top: 0.5rem; opacity: 0.75; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_config():
    with app_path("config.yaml").open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)

config = load_config()
embedding_config = config["embedding"]
vector_config = config["vector_store"]
FIXED_COLLECTION = "policylens_v1_fixed"
STRUCTURE_COLLECTION = "policylens_v1_structure"

@st.cache_resource
def load_embedder(model_name, batch_size, normalize_embeddings):
    return Embedder(model_name=model_name, batch_size=batch_size,
                    normalize_embeddings=normalize_embeddings)

embedder = load_embedder(embedding_config["model"],
    embedding_config.get("batch_size", 32),
    embedding_config.get("normalize_embeddings", True))

@st.cache_resource
def load_store(db_path, collection_name):
    return VectorStore(path=str(data_path(db_path)), collection_name=collection_name)

st.sidebar.title("⚖️ PolicyLens")
st.sidebar.caption("Regulatory Document Intelligence")
page = st.sidebar.radio("Navigate", ["Search", "Corpus Overview"])
st.sidebar.divider()
st.sidebar.markdown("**Retrieval Engine**")
st.sidebar.caption("Sentence Transformers")
st.sidebar.caption("ChromaDB")
st.sidebar.caption("Local regulatory corpus")
st.sidebar.divider()
st.sidebar.caption("Retrieval-only system")
st.sidebar.caption("No AI-generated legal advice")
st.markdown("""
<div class="hero"><h1>PolicyLens</h1><p>Search regulatory circulars using natural language.
Explore relevant passages with document, page and section traceability.</p></div>
""", unsafe_allow_html=True)

if page == "Search":
    st.subheader("Search Regulatory Documents")
    st.write("Enter a question to retrieve relevant passages from the indexed regulatory corpus.")
    query = st.text_area("What would you like to find?",
        placeholder="Example: What are the KYC requirements for regulated entities?", height=110)
    col1, col2 = st.columns(2)
    with col1:
        strategy = st.selectbox("Retrieval strategy", ["structure", "fixed", "compare"],
            format_func=lambda value: {"structure":"Structure-aware chunks",
                "fixed":"Fixed-size chunks", "compare":"Compare both strategies"}[value])
    with col2:
        top_k = st.slider("Number of results", 1, 10,
                          value=config["search"].get("default_top_k", 5))
    if st.button("Search documents", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a question before searching.")
        else:
            try:
                with st.spinner("Searching regulatory documents..."):
                    query_embedding = embedder.embed_texts([query])[0]
                    for selected in (["fixed", "structure"] if strategy == "compare" else [strategy]):
                        collection = FIXED_COLLECTION if selected == "fixed" else STRUCTURE_COLLECTION
                        st.divider()
                        st.subheader("Fixed-size retrieval results" if selected == "fixed"
                                     else "Structure-aware retrieval results")
                        results = load_store(vector_config["path"], collection).search(
                            query_embedding=query_embedding, top_k=top_k)
                        documents = results.get("documents", [[]])[0]
                        metadatas = results.get("metadatas", [[]])[0]
                        distances = results.get("distances", [[]])[0]
                        if not documents:
                            st.info("No matching passages were found.")
                            continue
                        st.caption(f"{len(documents)} matching passages retrieved from {collection}")
                        for index, (document, metadata, distance) in enumerate(
                                zip(documents, metadatas, distances), start=1):
                            score = 1 - float(distance)
                            title = metadata.get("title", "Untitled document")
                            issuer = metadata.get("issuer", "Unknown issuer")
                            start = metadata.get("page_start", "?")
                            end = metadata.get("page_end", start)
                            page_label = f"Page {start}" if start == end else f"Pages {start}–{end}"
                            with st.container(border=True):
                                st.markdown(f"**{index}. {title}**")
                                st.caption(f"{issuer} · {page_label}")
                                st.caption(f"Section: {metadata.get('section_title', 'Not specified')}")
                                st.progress(max(0.0, min(1.0, score)),
                                            text=f"Similarity score: {score:.4f}")
                                with st.expander("View retrieved passage"):
                                    st.write(document)
            except Exception as error:
                st.error(f"Search failed: {error}")

elif page == "Corpus Overview":
    st.subheader("Corpus Overview")
    st.write("A live snapshot of the indexed regulatory document collections.")
    try:
        fixed = load_store(vector_config["path"], FIXED_COLLECTION).count()
        structure = load_store(vector_config["path"], STRUCTURE_COLLECTION).count()
        col1, col2, col3 = st.columns(3)
        col1.metric("Fixed-size chunks", f"{fixed:,}")
        col2.metric("Structure-aware chunks", f"{structure:,}")
        col3.metric("Total indexed chunks", f"{fixed+structure:,}")
        st.divider()
        st.markdown("**Collection details**")
        st.table({"Retrieval strategy":["Fixed-size","Structure-aware"],
                  "Collection name":[FIXED_COLLECTION,STRUCTURE_COLLECTION],
                  "Indexed chunks":[fixed,structure]})
        if fixed and structure:
            st.success("Successfully connected to both populated ChromaDB collections.")
        else:
            st.warning("One or more collections are empty. Check the database path and collection names.")
        st.caption("Counts are read directly from your existing ChromaDB database. The dashboard does not modify your indexed documents.")
    except Exception as error:
        st.error(f"Could not load corpus information: {error}")

st.divider()
st.caption("PolicyLens | Regulatory Document Retrieval System")
