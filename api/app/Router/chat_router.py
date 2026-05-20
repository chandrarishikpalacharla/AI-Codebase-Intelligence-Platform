# =============================================================
# chat_router.py
# Same router works for BOTH Basic RAG and LlamaIndex
# Just change the import below
# =============================================================

from fastapi import APIRouter, UploadFile, File, WebSocket

# ---- USE ONE OF THESE ----
#from app.Service.ChatService import ChatServiceBasicRAG as ChatService   # Basic RAG
from app.Service.ChatService import ChatServiceLlamaIndex as ChatService    # LlamaIndex
# --------------------------

router = APIRouter(prefix='/api')

# step 1 - upload zip
@router.post('/upload')
async def upload(file: UploadFile = File(...)):
    session_id = await ChatService.process_upload(file)
    return {"session_id": session_id}

# step 2 - websocket chat
@router.websocket('/ws/chat/{session_id}')
async def chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    question = await websocket.receive_text()
    await ChatService.process_chat(websocket, session_id, question)