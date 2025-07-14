# Import required modules
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any

# Load variables from .env file
load_dotenv()

# Configure Gemini AI with the API key from .env
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create a model instance using Gemini 1.5 Flash
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Initialize the FastAPI app
app = FastAPI()

# Mount static files from "static" directory at /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Chat memory file path
CHAT_MEMORY_FILE = "chat_memory.json"

def load_chat_memory() -> List[Dict[str, Any]]:
    """Load chat memory from JSON file in the specified format"""
    try:
        if os.path.exists(CHAT_MEMORY_FILE):
            with open(CHAT_MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert old format to new format if needed
                if isinstance(data, dict):
                    # Convert session-based format to new format
                    chats = []
                    for session_id, session in data.items():
                        if session.get("messages"):  # Only include chats with messages
                            chat = {
                                "id": session_id,
                                "title": session.get("title", "New Chat"),
                                "date": session.get("created_at", datetime.now().isoformat()[:10]),
                                "messages": []
                            }
                            # Convert messages to the expected format
                            for msg in session.get("messages", []):
                                chat["messages"].extend([
                                    {"role": "user", "text": msg.get("user_message", "")},
                                    {"role": "ai", "text": msg.get("ai_response", "")}
                                ])
                            chats.append(chat)
                    return chats
                return data if isinstance(data, list) else []
        return []
    except Exception as e:
        print(f"Error loading chat memory: {e}")
        return []

def save_chat_memory(chats: List[Dict[str, Any]]) -> None:
    """Save chat memory to JSON file"""
    try:
        with open(CHAT_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(chats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving chat memory: {e}")

def get_chat_by_id(chat_id: str) -> Dict[str, Any]:
    """Get a specific chat by ID"""
    chats = load_chat_memory()
    for chat in chats:
        if chat.get("id") == chat_id:
            return chat
    return None

def create_new_chat() -> Dict[str, Any]:
    """Create a new chat session"""
    chats = load_chat_memory()
    new_chat = {
        "id": str(uuid.uuid4()),
        "title": "New Chat",
        "date": datetime.now().isoformat()[:10],
        "messages": []
    }
    chats.insert(0, new_chat)  # Add to beginning
    save_chat_memory(chats)
    return new_chat

def add_message_to_chat(chat_id: str, user_message: str, ai_response: str) -> bool:
    """Add a message to an existing chat"""
    chats = load_chat_memory()
    
    for chat in chats:
        if chat.get("id") == chat_id:
            # Add messages
            chat["messages"].extend([
                {"role": "user", "text": user_message},
                {"role": "ai", "text": ai_response}
            ])
            
            # Update title if this is the first message
            if len(chat["messages"]) == 2:  # First user + AI message
                chat["title"] = user_message[:50] + "..." if len(user_message) > 50 else user_message
            
            # Update date
            chat["date"] = datetime.now().isoformat()[:10]
            
            save_chat_memory(chats)
            return True
    
    return False

def rename_chat(chat_id: str, new_title: str) -> bool:
    """Rename a chat"""
    chats = load_chat_memory()
    
    for chat in chats:
        if chat.get("id") == chat_id:
            chat["title"] = new_title
            chat["date"] = datetime.now().isoformat()[:10]
            save_chat_memory(chats)
            return True
    
    return False

def delete_chat(chat_id: str) -> bool:
    """Delete a chat"""
    chats = load_chat_memory()
    original_length = len(chats)
    
    chats = [chat for chat in chats if chat.get("id") != chat_id]
    
    if len(chats) != original_length:
        save_chat_memory(chats)
        return True
    
    return False

def clear_all_chats() -> None:
    """Clear all chat history"""
    save_chat_memory([])

# GET route: Shows the chat UI
@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request, chat_id: str = None):
    chats = load_chat_memory()
    current_chat = None
    current_messages = []
    
    if chat_id:
        current_chat = get_chat_by_id(chat_id)
        if current_chat:
            current_messages = current_chat.get("messages", [])
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "chats": chats,
        "current_chat_id": chat_id,
        "current_messages": current_messages
    })

# POST route: Handles form submission
@app.post("/", response_class=HTMLResponse)
async def chat_message(request: Request, message: str = Form(...), chat_id: str = Form(None)):
    try:
        # Create new chat if no chat_id provided
        if not chat_id:
            new_chat = create_new_chat()
            chat_id = new_chat["id"]
        
        # Start a new chat session with Gemini model
        chat = model.start_chat()
        
        # Send user message to the Gemini model and get response
        response = chat.send_message(message)
        
        # Add message to chat
        add_message_to_chat(chat_id, message, response.text)
        
        # Get updated chat data
        current_chat = get_chat_by_id(chat_id)
        current_messages = current_chat.get("messages", []) if current_chat else []
        chats = load_chat_memory()
        
        # Render the page with the response
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": response.text,
            "message": message,
            "chats": chats,
            "current_chat_id": chat_id,
            "current_messages": current_messages
        })
        
    except Exception as e:
        chats = load_chat_memory()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "response": f"Error: {str(e)}",
            "message": message,
            "chats": chats,
            "current_chat_id": chat_id,
            "current_messages": []
        })

# API endpoint to get all chats
@app.get("/api/chats", response_class=JSONResponse)
async def get_chats():
    """Get all chat sessions"""
    chats = load_chat_memory()
    return {"chats": chats}

# API endpoint to get a specific chat
@app.get("/api/chats/{chat_id}", response_class=JSONResponse)
async def get_chat(chat_id: str):
    """Get a specific chat with all its messages"""
    chat = get_chat_by_id(chat_id)
    if chat:
        return {"chat": chat}
    else:
        raise HTTPException(status_code=404, detail="Chat not found")

# API endpoint to create a new chat
@app.post("/api/chats/new", response_class=JSONResponse)
async def create_new_chat_api():
    """Create a new empty chat"""
    new_chat = create_new_chat()
    return {"success": True, "chat": new_chat}

# API endpoint to add a message to a chat
@app.post("/api/chats/{chat_id}/messages", response_class=JSONResponse)
async def add_message(chat_id: str, request: Request):
    """Add a message to a chat"""
    try:
        body = await request.json()
        user_message = body.get("user_message", "").strip()
        ai_response = body.get("ai_response", "").strip()
        
        if not user_message or not ai_response:
            raise HTTPException(status_code=400, detail="Both user_message and ai_response are required")
        
        success = add_message_to_chat(chat_id, user_message, ai_response)
        if success:
            return {"success": True, "message": "Message added successfully"}
        else:
            raise HTTPException(status_code=404, detail="Chat not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding message: {str(e)}")

# API endpoint to rename a chat
@app.put("/api/chats/{chat_id}/rename", response_class=JSONResponse)
async def rename_chat_api(chat_id: str, request: Request):
    """Rename a chat"""
    try:
        body = await request.json()
        new_title = body.get("title", "").strip()
        
        if not new_title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        
        success = rename_chat(chat_id, new_title)
        if success:
            return {"success": True, "message": "Chat renamed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Chat not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renaming chat: {str(e)}")

# API endpoint to delete a chat
@app.delete("/api/chats/{chat_id}", response_class=JSONResponse)
async def delete_chat_api(chat_id: str):
    """Delete a chat"""
    success = delete_chat(chat_id)
    if success:
        return {"success": True, "message": "Chat deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Chat not found")

# API endpoint to clear all chats
@app.delete("/api/chats", response_class=JSONResponse)
async def clear_all_chats_api():
    """Clear all chat history"""
    clear_all_chats()
    return {"success": True, "message": "All chats cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
