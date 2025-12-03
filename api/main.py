from fastapi import FastAPI
from api.routers import auth, ideas, webhooks
from database.connection import init_db

app = FastAPI(title="Idea Validator API", version="0.1.0")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"status": "online", "message": "Idea Validator is running"}

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(ideas.router, prefix="/ideas", tags=["Ideas"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
