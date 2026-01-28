from fastapi import FastAPI
from app.api.routes import auth, users
from app.api.routes import chats
from app.api.routes import ws
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="TempleChat")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(ws.router)



@app.get("/health")
async def health():
    return {"status": "ok"}