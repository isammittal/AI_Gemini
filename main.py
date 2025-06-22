import os
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Load environment variables
load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("models/gemini-1.5-flash")

app = FastAPI()

# Setup HTML and CSS support
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "response": None})


@app.post("/", response_class=HTMLResponse)
async def chat_message(request: Request, message: str = Form(...)):
    try:
        chat = model.start_chat()
        response = chat.send_message(message)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": response.text,
            "message": message
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": f"Error: {str(e)}",
            "message": message
        })
