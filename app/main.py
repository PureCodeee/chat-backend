from fastapi import FastAPI
from app.api.routes import auth, users
from app.api.routes import chats
from app.api.routes import ws
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.db.session import engine
from app.db.base import Base


app = FastAPI(title="TempleChat")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(ws.router)


@app.get("/")
def root():
    return RedirectResponse("/static/login.html")


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
