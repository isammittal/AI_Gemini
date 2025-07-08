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
def load_chat_memory() -> Dict[str, Dict[str, Any]]:
    """Load chat memory from JSON file, organized by session ID"""
    try:
        if os.path.exists(CHAT_MEMORY_FILE):
            with open(CHAT_MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert to session-based format if it's the old format
                if isinstance(data, list):
                    return convert_to_session_format(data)
                elif isinstance(data, dict) and any(isinstance(v, list) for v in data.values()):
                    return convert_date_format_to_session(data)
                return data
        return {}
    except Exception as e:
        print(f"Error loading chat memory: {e}")
        return {}

def convert_to_session_format(memory_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Convert old list format to session-based format"""
    sessions = {}
    for entry in memory_list:
        session_id = entry.get('session_id', str(uuid.uuid4()))
        if session_id not in sessions:
            sessions[session_id] = {
                "session_id": session_id,
                "title": entry.get('summary', 'New Chat'),
                "created_at": entry.get('timestamp', datetime.now().isoformat()),
                "last_updated": entry.get('timestamp', datetime.now().isoformat()),
                "messages": []
            }
        
        sessions[session_id]["messages"].append({
            "user_message": entry.get('user_message', ''),
            "ai_response": entry.get('ai_response', ''),
            "timestamp": entry.get('timestamp', datetime.now().isoformat())
        })
        sessions[session_id]["last_updated"] = entry.get('timestamp', datetime.now().isoformat())
    
    return sessions

def convert_date_format_to_session(date_memory: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """Convert date-grouped format to session-based format"""
    sessions = {}
    for date, chats in date_memory.items():
        for chat in chats:
            session_id = chat.get('session_id', str(uuid.uuid4()))
            if session_id not in sessions:
                sessions[session_id] = {
                    "session_id": session_id,
                    "title": chat.get('summary', 'New Chat'),
                    "created_at": chat.get('timestamp', datetime.now().isoformat()),
                    "last_updated": chat.get('timestamp', datetime.now().isoformat()),
                    "messages": []
                }
            
            sessions[session_id]["messages"].append({
                "user_message": chat.get('user_message', ''),
                "ai_response": chat.get('ai_response', ''),
                "timestamp": chat.get('timestamp', datetime.now().isoformat())
            })
            sessions[session_id]["last_updated"] = chat.get('timestamp', datetime.now().isoformat())
    
    return sessions

def save_chat_memory(memory: Dict[str, Dict[str, Any]]) -> None:
    """Save chat memory to JSON file"""
    try:
        with open(CHAT_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving chat memory: {e}")

def get_or_create_session(session_id: str = None) -> str:
    """Get existing session ID or create a new one"""
    if session_id:
        memory = load_chat_memory()
        if session_id in memory:
            return session_id
    
    return str(uuid.uuid4())

def add_message_to_session(session_id: str, user_message: str, ai_response: str) -> str:
    """Add a message to an existing session or create a new session"""
    memory = load_chat_memory()
    
    # If session doesn't exist, create it
    if session_id not in memory:
        memory[session_id] = {
            "session_id": session_id,
            "title": user_message[:50] + "..." if len(user_message) > 50 else user_message,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "messages": []
        }
    
    # Add the message to the session
    memory[session_id]["messages"].append({
        "user_message": user_message,
        "ai_response": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update the last_updated timestamp
    memory[session_id]["last_updated"] = datetime.now().isoformat()
    
    # Update title if this is the first message
    if len(memory[session_id]["messages"]) == 1:
        memory[session_id]["title"] = user_message[:50] + "..." if len(user_message) > 50 else user_message
    
    # Save to file
    save_chat_memory(memory)
    
    return session_id

def delete_session(session_id: str) -> bool:
    """Delete a session from memory"""
    memory = load_chat_memory()
    
    if session_id in memory:
        del memory[session_id]
        save_chat_memory(memory)
        return True
    return False

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """Get all messages for a specific session"""
    memory = load_chat_memory()
    if session_id in memory:
        return memory[session_id]["messages"]
    return []

# Load initial memory
chat_memory = load_chat_memory()

# GET route: Shows the empty chat UI when user visits the root URL
@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request, session_id: str = None):
    memory = load_chat_memory()
    
    # Get current session messages if session_id is provided
    current_messages = []
    if session_id:
        current_messages = get_session_messages(session_id)
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "response": None,
        "chat_memory": memory,
        "current_session_id": session_id,
        "current_messages": current_messages
    })

# POST route: Handles form submission from the chat UI
@app.post("/", response_class=HTMLResponse)
async def chat_message(request: Request, message: str = Form(...), session_id: str = Form(None)):
    try:
        # Get or create session ID
        current_session_id = get_or_create_session(session_id)
        
        # Start a new chat session with Gemini model
        chat = model.start_chat()

        # Send user message to the Gemini model and get response
        response = chat.send_message(message)

        # Add message to session
        add_message_to_session(current_session_id, message, response.text)
        
        # Load updated memory
        memory = load_chat_memory()
        current_messages = get_session_messages(current_session_id)

        # Render the same page with the user message and AI response
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": response.text,  # Gemini's reply
            "message": message,  # User's message
            "chat_memory": memory,
            "current_session_id": current_session_id,
            "current_messages": current_messages
        })
    except Exception as e:
        # If there's any error, show the error on the same page
        memory = load_chat_memory()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": f"Error: {str(e)}",
            "message": message,
            "chat_memory": memory,
            "current_session_id": session_id,
            "current_messages": []
        })

# API endpoint to get chat memory (for AJAX requests)
@app.get("/api/memory", response_class=JSONResponse)
async def get_memory():
    """Get all chat memory sessions"""
    memory = load_chat_memory()
    return {"memory": memory}

# API endpoint to get a specific session
@app.get("/api/memory/{session_id}", response_class=JSONResponse)
async def get_session(session_id: str):
    """Get a specific session with all its messages"""
    memory = load_chat_memory()
    if session_id in memory:
        return {"session": memory[session_id]}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

# API endpoint to delete a session
@app.delete("/api/memory/{session_id}", response_class=JSONResponse)
async def delete_memory(session_id: str):
    """Delete a specific session"""
    success = delete_session(session_id)
    if success:
        return {"success": True, "message": "Session deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

# API endpoint to create a new session
@app.post("/api/memory/new", response_class=JSONResponse)
async def create_new_session():
    """Create a new empty session"""
    session_id = str(uuid.uuid4())
    memory = load_chat_memory()
    
    memory[session_id] = {
        "session_id": session_id,
        "title": "New Chat",
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "messages": []
    }
    
    save_chat_memory(memory)
    return {"success": True, "session_id": session_id, "message": "New session created"}

# API endpoint to clear all chat memory
@app.delete("/api/memory", response_class=JSONResponse)
async def clear_memory():
    """Clear all chat memory"""
    save_chat_memory({})
    return {"success": True, "message": "All chat history cleared"}
