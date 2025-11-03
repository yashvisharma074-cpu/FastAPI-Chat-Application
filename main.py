from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from router import auth_routers, chat_routers
from core.database import Base, engine
from core.security import get_current_user
import os

# === App Initialization ===
app = FastAPI(title="FastAPI Chat App")

# === Uploads Directory ===
UPLOAD_DIR = "uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === Database Create Tables ===
Base.metadata.create_all(bind=engine)

# === Mount Static and Uploads Folders ===
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# === Templates ===
templates = Jinja2Templates(directory="template")


# === Routes ===

@app.get("/", response_class=HTMLResponse)
def home():
    """Redirect root to login page"""
    return RedirectResponse(url="/login")


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """Registration Page"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Login Page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
def chat_page(
    request: Request,
    current_user=Depends(get_current_user)
):
    """Chat Page — only accessible by logged-in user"""
    print(f"✅ Current User → {current_user.username}")
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "current_user_id": current_user.id,
            "current_username": current_user.username,
        },
    )


# === Include Routers ===
app.include_router(auth_routers.router, prefix="/auth", tags=["Auth"])
app.include_router(chat_routers.router, prefix="/chat", tags=["Chat"])


# === Run Server (optional) ===
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
