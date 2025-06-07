from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup Jinja templates
templates = Jinja2Templates(directory="../frontend/html")

# Check for secret key
SECRET_KEY = os.getenv("SESSION_SECRET")
if not SECRET_KEY:
    raise Exception("SESSION_SECRET not set in environment variables!")

# CORS settings
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Initialize FastAPI app
app = FastAPI(
    title="SwaadSathi API",
    description="A Full Stack Recipe & Health Assistant App",
    version="1.0.0"
)

# Middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
app.mount("/uploaded_images", StaticFiles(directory="uploaded_images"), name="uploaded_images")

# Routers
from auth import router as auth_router
from recipes import router as recipe_router
from ai_recipe import router as gemini_router
from health import router as health_router
from image_scan import router as image_router
from profile import router as profile_router
from contact import router as contact_router

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(recipe_router, prefix="/recipes", tags=["Recipes"])
app.include_router(gemini_router, prefix="/ai", tags=["AI Recipes"])
app.include_router(health_router, prefix="/health", tags=["Health & Diet"])
app.include_router(profile_router, prefix="/profile", tags=["User Profile"])
app.include_router(image_router, tags=["Image & Barcode"])
app.include_router(contact_router)

# API health check (for Postman etc.)
@app.get("/api", tags=["Root"])
async def root():
    return {"message": "Welcome to the SwaadSathi API 🚀"}

# Frontend homepage route
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# Frontend login/signup page
@app.get("/login_signup", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse("login_signup.html", {"request": request})
