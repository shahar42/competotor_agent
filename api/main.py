from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routers import auth, ideas, webhooks
from database.connection import init_db
import os

app = FastAPI(title="Idea Validator API", version="0.1.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(ideas.router, prefix="/ideas", tags=["Ideas"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
