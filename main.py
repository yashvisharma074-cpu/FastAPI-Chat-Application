from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from router import auth_routers, chat_routers
from core.database import Base, engine
from core.security import get_current_user
import uvicorn

app = FastAPI(title="FastAPI Chat App")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template") 


@app.get("/", response_class=HTMLResponse)
def home():
    return RedirectResponse(url="/login")


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
def chat_page(
    request: Request,
    current_user=Depends(get_current_user) 
):
    print('current_user', current_user)
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "current_user_id": current_user.id}
    )


app.include_router(auth_routers.router, prefix="/auth", tags=["Auth"])
app.include_router(chat_routers.router, prefix="/chat", tags=["Chat"])


