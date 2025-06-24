# Import required modules
import os  # For accessing environment variables
from dotenv import load_dotenv  # To load .env file and its variables
import google.generativeai as genai  # Google's Gemini model for AI
from fastapi import FastAPI, Request, Form  # FastAPI tools for web app
from fastapi.responses import HTMLResponse  # To return HTML as response
from fastapi.staticfiles import StaticFiles  # To serve static files like CSS
from fastapi.templating import Jinja2Templates  # To render HTML templates using Jinja2

# Load variables from .env file (like API key)
load_dotenv()

# Configure Gemini AI with the API key from .env
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create a model instance using Gemini 1.5 Flash
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Initialize the FastAPI app
app = FastAPI()

# Mount static files (like CSS, JS) from "static" directory at /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates directory (HTML files will be picked from here)
templates = Jinja2Templates(directory="templates")


# GET route: Shows the empty chat UI when user visits the root URL
@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "response": None})


# POST route: Handles form submission from the chat UI
@app.post("/", response_class=HTMLResponse)
async def chat_message(request: Request, message: str = Form(...)):
    try:
        # Start a new chat session with Gemini model
        chat = model.start_chat()

        # Send user message to the Gemini model and get response
        response = chat.send_message(message)

        # Render the same page with the user message and AI response
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": response.text,  # Gemini's reply
            "message": message  # User's message
        })
    except Exception as e:
        # If there's any error, show the error on the same page
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": f"Error: {str(e)}",
            "message": message
        })
