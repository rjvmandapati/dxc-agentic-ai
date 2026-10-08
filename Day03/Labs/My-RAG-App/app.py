import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import streamlit as st
from pypdf import PdfReader
from datetime import datetime

from askit_core import bedrock, config

st.set_page_config(page_title="Ask Buddy", page_icon="🎩", layout="wide")

# This styling gives the requested dark teal look without changing Streamlit behavior.
st.markdown("""
<style>
    :root { color-scheme: dark; }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] { background: #071a1d; color: #eaf8f5; }
    .block-container { padding-top: 1.2rem; padding-bottom: 5rem; }
    h1, h2, h3 { color: #5eead4 !important; }
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"] { color: #eaf8f5; }
    [data-testid="stChatMessage"], [data-testid="stExpander"] { background: #103238; color: #eaf8f5; border: 1px solid #2b6567; border-radius: 10px; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p, [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p { color: #eaf8f5; }
    div[data-testid="stChatInput"] textarea { background: #103238; color: #f0fdfa !important; -webkit-text-fill-color: #f0fdfa; caret-color: #5eead4; }
    div[data-testid="stChatInput"] textarea::placeholder { color: #b3ceca !important; -webkit-text-fill-color: #b3ceca; opacity: 1; }
    div[data-testid="stChatInput"]:focus-within { border-color: #2dd4bf; box-shadow: 0 0 0 1px #2dd4bf; }
    div[data-testid="stFileUploader"] section { background: #103238; color: #eaf8f5; border: 1px dashed #5b9993; border-radius: 10px; }
    .stButton > button, .stDownloadButton > button, div[data-testid="stFileUploader"] button { background: #2dd4bf !important; color: #062b2e !important; -webkit-text-fill-color: #062b2e; border: 0; border-radius: 8px; }
    .stButton > button *, .stDownloadButton > button *, div[data-testid="stFileUploader"] button * { color: #062b2e !important; fill: #062b2e !important; }
    .stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stFileUploader"] button:hover { background: #5eead4 !important; }
    .stButton > button:focus-visible, .stDownloadButton > button:focus-visible, div[data-testid="stFileUploader"] button:focus-visible { outline: 2px solid #f0fdfa; outline-offset: 2px; }
    [data-testid="stAlert"] { background: #103238; color: #eaf8f5; border: 1px solid #2b6567; }
    [data-testid="stAlert"] p, [data-testid="stAlert"] span { color: #eaf8f5 !important; }
    [data-testid="stSlider"] { color: #eaf8f5; }
    [data-testid="stProgressBar"] { color: #5eead4; accent-color: #2dd4bf; }
    .about-card { background: #d8f5ef; color: #123b3b; border-left: 4px solid #2dd4bf; border-radius: 8px; padding: 12px; }
    .about-card * { color: #123b3b !important; }
    .app-footer { color: #b3ceca; text-align: center; padding: 2rem 0 0.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("🎩 Ask Buddy")
st.caption("Upload. Ask. Done.")

# Session state keeps the index and conversation across Streamlit reruns.
st.session_state.setdefault("chat", [])
st.session_state.setdefault("index", None)
st.session_state.setdefault("pdf_id", None)
st.session_state.setdefault("chunk_size", 120)
st.session_state.setdefault("overlap", 30)

with st.sidebar:
    st.header("About me")
    st.markdown(f"<div class='about-card'><b>Rajeev</b><br>{datetime.now():%d %b %Y}<br><br>I turn PDFs into answers, one page at a time.</div>", unsafe_allow_html=True)
    st.slider("Top-K", 1, 6, 3, key="top_k")
    st.slider("Chunk size", 60, 200, key="chunk_size")
    st.slider("Overlap", 0, 60, key="overlap")
    st.button("Clear chat", on_click=lambda: st.session_state.chat.clear())


# Word chunks preserve page boundaries so every source can be cited correctly.
def chunk_text(text, size, overlap):
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += max(1, size - overlap)
    return chunks


# Titan requests are sent in small batches to limit shared-account load.
def embed_texts(texts, progress=None):
    client = bedrock.client()
    vecs = []
    for start in range(0, len(texts), 4):
        for offset, text in enumerate(texts[start:start + 4], start=start):
            body = {"inputText": text, "dimensions": 512, "normalize": True}
            response = client.invoke_model(modelId="amazon.titan-embed-text-v2:0", body=json.dumps(body))
            vecs.append(json.loads(response["body"].read())["embedding"])
            if progress:
                progress.progress(0.2 + 0.75 * (offset + 1) / len(texts), text=f"Embedding chunk {offset + 1} of {len(texts)}...")
    return np.array(vecs, dtype=float)


# Cosine similarity ranks the chunks by meaning rather than exact wording.
def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


# Reading each page separately keeps the original page number on each chunk.
def build_index(uploaded_file, size, overlap, progress):
    reader = PdfReader(uploaded_file)
    chunks = []
    for idx, page in enumerate(reader.pages, start=1):
        txt = page.extract_text() or ""
        if txt.strip():
            chunks.extend({"page": idx, "text": part} for part in chunk_text(txt, size, overlap))
        progress.progress(0.2 * idx / len(reader.pages), text=f"Reading page {idx} of {len(reader.pages)}...")
    if not chunks:
        return len(reader.pages), [], None
    vectors = embed_texts([part["text"] for part in chunks], progress)
    return len(reader.pages), chunks, vectors


# A changed upload replaces its old index and starts a fresh conversation.
uploaded = st.file_uploader("Upload a PDF", type="pdf")
pdf_id = hashlib.sha256(uploaded.getvalue()).hexdigest() if uploaded else None
if pdf_id != st.session_state.pdf_id:
    st.session_state.pdf_id = pdf_id
    st.session_state.index = None
    st.session_state.chat.clear()

if uploaded is not None:
    if st.button("Build index"):
        st.session_state.index = None
        st.session_state.chat.clear()
        progress = st.progress(0, text="Starting index build...")
        try:
            page_count, chunks, vectors = build_index(uploaded, st.session_state.chunk_size, st.session_state.overlap, progress)
            if not chunks:
                progress.empty()
                st.warning("No selectable text was found. This may be a scanned PDF; please upload a text-based PDF.")
            else:
                st.session_state.index = {"chunks": chunks, "vectors": vectors, "settings": (st.session_state.chunk_size, st.session_state.overlap)}
                progress.progress(1.0, text="Index ready")
                st.success(f"Indexed {page_count} pages and {len(chunks)} chunks.")
        except Exception:
            st.error("AWS check failed. Please verify your .env keys, AWS region, and Titan access. Then retry.")

settings = (st.session_state.chunk_size, st.session_state.overlap)
index_ready = st.session_state.index is not None and st.session_state.index["settings"] == settings
if st.session_state.index and not index_ready:
    st.info("Chunk settings changed. Click Build index to apply them before asking.")

# Show saved turns first so the bottom-docked chat box cannot cover the conversation.
if index_ready:
    for item in st.session_state.chat:
        with st.chat_message("user"):
            st.write(item["user"])
        with st.chat_message("assistant", avatar="🎩"):
            st.markdown(f"<span style='color:#7dd3fc'>[{item['badge']}]</span>", unsafe_allow_html=True)
            st.write(item["answer"])
            with st.expander("Sources"):
                for score, chunk in item["sources"]:
                    st.markdown(f"**Page {chunk['page']}** - similarity: {score:.2f}")
                    st.write(chunk["text"])

    demo_clicked = st.button("Not in my PDF?")
    question = st.chat_input("Ask about the PDF")
    if demo_clicked:
        question = "Who won the last cricket world cup?"
    if question:
        try:
            qvec = embed_texts([question])[0]
            index = st.session_state.index
            sims = []
            for i, chunk in enumerate(index["chunks"]):
                sim = cosine(qvec, index["vectors"][i])
                sims.append((sim, chunk))
            top = sorted(sims, key=lambda item: item[0], reverse=True)[:st.session_state.top_k]
            context = "\n\n".join(f"[p.{chunk['page']}] {chunk['text']}" for _, chunk in top)
            prompt = ("You are a formal, polite assistant. Answer ONLY from the context. If the answer is not in the context, "
                      "say you could not find it in the PDF. Cite the page like [p.3]. Do not use outside knowledge.\n\n"
                      f"Context:\n{context}\n\nQuestion:\n{question}")
            client = bedrock.client()
            response = client.converse(
                modelId=config.SMALL_MODEL,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 500, "temperature": 0.2},
            )
            answer = response["output"]["message"]["content"][0]["text"]
            badge = "grounded" if top and top[0][0] >= 0.35 else "weak match"
            st.session_state.chat.append({"user": question, "answer": answer, "sources": top, "badge": badge})
            st.rerun()
        except Exception:
            st.error("AWS check failed. Please verify your .env keys, AWS region, and Titan access. Then retry.")

# Markdown export contains the conversation and its cited source snippets.
if st.session_state.chat:
    transcript = "\n\n".join(f"## Question\n{turn['user']}\n\n## Answer ({turn['badge']})\n{turn['answer']}" for turn in st.session_state.chat)
    st.download_button("Download chat as Markdown", transcript, file_name="ask-buddy-chat.md", mime="text/markdown")

if not index_ready:
    st.info("Upload a PDF, build the index, and ask a question.")

st.markdown("<div class='app-footer'>Built by Rajeev with vibe coding at DevPro Academy</div>", unsafe_allow_html=True)
