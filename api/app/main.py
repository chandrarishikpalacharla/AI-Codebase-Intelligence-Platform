from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.Router.User import router as user_router   # ← add this
from app.Router.chat_router import router as chat_router

app = FastAPI()


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # react runs here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(user_router)   # ← add this
app.include_router(chat_router)

@app.get("/")
def home():
    return {"message": "fast api"}