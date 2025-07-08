# Import required modules
import os  # For accessing environment variables
import json  # For storing chat memory
import uuid  # For generating unique session IDs
from datetime import datetime  # For timestamps
from dotenv import load_dotenv  # To load .env file and its variables
import google.generativeai as genai  # Google's Gemini model for AI
from fastapi import FastAPI, Request, Form, HTTPException  # FastAPI tools for web app
from fastapi.responses import HTMLResponse, JSONResponse  # To return HTML and JSON responses
from fastapi.staticfiles import StaticFiles  # To serve static files like CSS
from fastapi.templating import Jinja2Templates  # To render HTML templates using Jinja2
from typing import List, Dict, Any  # Type hints
from collections import defaultdict

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

# Chat memory file path
CHAT_MEMORY_FILE = "chat_memory.json"

# Initialize chat memory
def load_chat_memory() -> Dict[str, List[Dict[str, Any]]]:
    """Load chat memory from JSON file, grouped by date"""
    try:
        if os.path.exists(CHAT_MEMORY_FILE):
            with open(CHAT_MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert to date-grouped format if it's the old format
                if isinstance(data, list):
                    return group_memory_by_date(data)
                return data
        return {}
    except Exception as e:
        print(f"Error loading chat memory: {e}")
        return {}

def group_memory_by_date(memory_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group memory entries by date"""
    grouped = defaultdict(list)
    for entry in memory_list:
        date = entry.get('timestamp', '').split('T')[0] if entry.get('timestamp') else datetime.now().strftime('%Y-%m-%d')
        grouped[date].append(entry)
    return dict(grouped)

def save_chat_memory(memory: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save chat memory to JSON file"""
    try:
        with open(CHAT_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving chat memory: {e}")

def add_chat_memory(user_message: str, ai_response: str) -> str:
    """Add a new chat to memory and return session ID"""
    memory = load_chat_memory()
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Create chat entry
    chat_entry = {
        "session_id": session_id,
        "user_message": user_message,
        "ai_response": ai_response,
        "timestamp": datetime.now().isoformat(),
        "summary": user_message[:50] + "..." if len(user_message) > 50 else user_message
    }
    
    # Add to today's date group
    if today not in memory:
        memory[today] = []
    memory[today].append(chat_entry)
    
    # Save to file
    save_chat_memory(memory)
    
    return session_id

def delete_chat_memory_by_date(date: str) -> bool:
    """Delete all chats from a specific date"""
    memory = load_chat_memory()
    
    if date in memory:
        del memory[date]
        save_chat_memory(memory)
        return True
    return False

def delete_chat_memory(session_id: str) -> bool:
    """Delete a chat from memory by session ID"""
    memory = load_chat_memory()
    
    # Find and remove the chat entry from any date
    for date, chats in memory.items():
        original_length = len(chats)
        memory[date] = [chat for chat in chats if chat["session_id"] != session_id]
        
        if len(memory[date]) < original_length:
            # If this date has no more chats, remove the date entry
            if len(memory[date]) == 0:
                del memory[date]
            save_chat_memory(memory)
            return True
    return False

# Load initial memory
chat_memory = load_chat_memory()

# GET route: Shows the empty chat UI when user visits the root URL
@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    memory = load_chat_memory()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "response": None,
        "chat_memory": memory
    })

# POST route: Handles form submission from the chat UI
@app.post("/", response_class=HTMLResponse)
async def chat_message(request: Request, message: str = Form(...)):
    try:
        # Start a new chat session with Gemini model
        chat = model.start_chat()

        # Send user message to the Gemini model and get response
        response = chat.send_message(message)

        # Add to chat memory
        session_id = add_chat_memory(message, response.text)
        
        # Load updated memory
        memory = load_chat_memory()

        # Render the same page with the user message and AI response
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": response.text,  # Gemini's reply
            "message": message,  # User's message
            "chat_memory": memory,
            "new_session_id": session_id
        })
    except Exception as e:
        # If there's any error, show the error on the same page
        memory = load_chat_memory()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": f"Error: {str(e)}",
            "message": message,
            "chat_memory": memory
        })

# API endpoint to get chat memory (for AJAX requests)
@app.get("/api/memory", response_class=JSONResponse)
async def get_memory():
    """Get all chat memory entries grouped by date"""
    memory = load_chat_memory()
    return {"memory": memory}

# API endpoint to delete a chat memory entry
@app.delete("/api/memory/{session_id}", response_class=JSONResponse)
async def delete_memory(session_id: str):
    """Delete a specific chat memory entry"""
    success = delete_chat_memory(session_id)
    if success:
        return {"success": True, "message": "Chat deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Chat not found")

# API endpoint to delete memory by date
@app.delete("/api/memory/date/{date}", response_class=JSONResponse)
async def delete_memory_by_date(date: str):
    """Delete all chat memory for a specific date"""
    success = delete_chat_memory_by_date(date)
    if success:
        return {"success": True, "message": f"All chats for {date} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Date not found")

# API endpoint to clear all chat memory
@app.delete("/api/memory", response_class=JSONResponse)
async def clear_memory():
    """Clear all chat memory"""
    save_chat_memory({})
    return {"success": True, "message": "All chat history cleared"}
