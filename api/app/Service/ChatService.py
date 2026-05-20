# =============================================================
# ChatService.py — Basic RAG vs LlamaIndex (for study)
# =============================================================

import os, uuid, tempfile
import zipfile
import shutil
from dotenv import load_dotenv
from fastapi import WebSocket

load_dotenv()

ALLOWED = {".py", ".java", ".js", ".ts", ".html", ".css", ".md"}
SKIP_FOLDERS = {"node_modules", ".git", "build", "dist", "target", "__pycache__"}

sessions = {}


# =============================================================
# APPROACH 1 — BASIC RAG (manual)
# =============================================================
# You write everything yourself:
# chunking, embedding, chromadb, search, groq call
# =============================================================

from sentence_transformers import SentenceTransformer
from groq import Groq
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ChatServiceBasicRAG:

    @staticmethod
    async def process_upload(file):

        session_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp()

        # save zip
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(await file.read())

        # unzip
        extract_path = os.path.join(temp_dir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_path)

        # ---- MANUAL CHUNKING ----
        # split every 500 chars (blind splitting)
        chunks = []
        for root, dirs, files in os.walk(extract_path):
            dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS]
            for fileName in files:
                ext = os.path.splitext(fileName)[1].lower()
                if ext not in ALLOWED:
                    continue
                file_path = os.path.join(root, fileName)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for i in range(0, len(content), 500):
                    chunk = content[i:i + 500]
                    if chunk.strip():
                        chunks.append({"text": chunk, "file": fileName})

        # ---- MANUAL EMBEDDING ----
        # sentence-transformers converts text to vectors
        texts = [c["text"] for c in chunks]
        embeddings = model.encode(texts)

        # ---- MANUAL CHROMADB ----
        # store vectors manually
        client = chromadb.Client()
        collection = client.create_collection(session_id)
        collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=[{"file": c["file"]} for c in chunks],
            ids=[str(i) for i in range(len(chunks))]
        )

        sessions[session_id] = {
            "client": client,
            "collection": collection,
            "temp_dir": temp_dir
        }

        return session_id

    @staticmethod
    async def process_chat(websocket: WebSocket, session_id: str, question: str):

        session = sessions.get(session_id)
        if not session:
            await websocket.send_text("Session not found")
            await websocket.close()
            return

        try:
            await websocket.send_text("🔍 Searching codebase...")

            # ---- MANUAL SEARCH ----
            # find top 5 similar chunks
            collection = session["collection"]
            result = collection.query(query_texts=[question], n_results=5)
            relevant_chunks = result["documents"][0]
            context = "\n\n".join(relevant_chunks)

            await websocket.send_text("💡 Generating answer...")

            # ---- MANUAL GROQ CALL ----
            # build prompt manually and call groq
            stream = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a code assistant. Answer based on context only."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ],
                stream=True
            )

            # stream word by word
            for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    await websocket.send_text(token)

        finally:
            await websocket.close()
            shutil.rmtree(session["temp_dir"], ignore_errors=True)
            try:
                session["client"].delete_collection(session_id)
            except:
                pass
            sessions.pop(session_id, None)


# =============================================================
# APPROACH 2 — LLAMAINDEX (automatic)
# =============================================================
# LlamaIndex does everything automatically:
# smart chunking, embedding, vector store, search, LLM call
# You write 5 lines instead of 100+
# Extra features: file citations, better search, smart chunking
# =============================================================

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.groq import Groq as LlamaGroq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# setup once at startup
Settings.llm = LlamaGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


class ChatServiceLlamaIndex:

    @staticmethod
    async def process_upload(file):

        session_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp()

        try:
            # save zip
            zip_path = os.path.join(temp_dir, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(await file.read())

            # unzip
            extract_path = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(extract_path)

            # skip heavy folders
            for root, dirs, files in os.walk(extract_path):
                dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS]

            # ---- LLAMAINDEX DOES ALL THIS AUTOMATICALLY ----
            # reads files + smart chunking + embedding + vector store
            documents = SimpleDirectoryReader(
                input_dir=extract_path,
                recursive=True,
                required_exts=list(ALLOWED)
            ).load_data()

            index = VectorStoreIndex.from_documents(documents)
            # -------------------------------------------------

            sessions[session_id] = {
                "index": index,
                "temp_dir": temp_dir
            }

            print(f"Session saved: {session_id}")
            print(f"Total docs loaded: {len(documents)}")

            return session_id

        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    @staticmethod
    async def process_chat(websocket: WebSocket, session_id: str, question: str):

        session = sessions.get(session_id)
        if not session:
            await websocket.send_text("Session not found")
            await websocket.close()
            return

        try:
            await websocket.send_text("🔍 Searching codebase...")

            index = session["index"]

            # ---- LLAMAINDEX SEARCH + LLM CALL AUTOMATIC ----
            query_engine = index.as_query_engine(
                similarity_top_k=5,
                streaming=True
            )

            await websocket.send_text("💡 Generating answer...")

            response = query_engine.query(question)

            # ---- FILE CITATIONS (extra feature, not in basic RAG) ----
            sources = set()
            for node in response.source_nodes:
                fname = node.metadata.get("file_name", "unknown")
                sources.add(fname)

            citation = "📁 Found in: " + ", ".join(sources)
            await websocket.send_text(citation + "\n\n")

            # stream answer word by word
            for token in response.response_gen:
                if token:
                    await websocket.send_text(token)

        finally:
            await websocket.close()
            shutil.rmtree(session["temp_dir"], ignore_errors=True)
            sessions.pop(session_id, None)


# =============================================================
# COMPARISON SUMMARY
# =============================================================
#
# | Step          | Basic RAG          | LlamaIndex         |
# |---------------|--------------------|--------------------|
# | Read files    | manual os.walk     | SimpleDirectoryReader|
# | Chunking      | every 500 chars    | smart by paragraph |
# | Embedding     | sentence-transformers | HuggingFaceEmbedding|
# | Vector store  | ChromaDB manual    | built in automatic |
# | Search        | collection.query() | query_engine.query()|
# | LLM call      | groq manual        | built in           |
# | Citations     | ❌ not available   | ✅ source_nodes    |
# | Lines of code | 100+               | ~10                |
#
# Both work. LlamaIndex is smarter and less code.
# Basic RAG is better for learning internals.
# =============================================================