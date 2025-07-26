# Sam's AI Chatbot 🤖

A modern AI chatbot built with FastAPI and Gemini AI, featuring a clean chat interface with memory management and text-to-speech support.

## ✨ Features

### 🤖 AI Chatbot

- Powered by Google Gemini 1.5 Flash
- Real-time chat interface with typing animations
- Chat history and memory management
- Text-to-speech support
- Mobile-responsive design
- Clean, modern UI

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd Gemini_AI_ChatBot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Gemini AI API Key
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

### 5. Run the Application

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the Application

- Open your browser to `http://localhost:8000`
- Start chatting with the AI!

## 📁 Project Structure

```
Gemini_AI_ChatBot/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create from env.example)
├── chat_memory.json    # Chat history storage
├── static/
│   ├── style.css       # Main styles
│   └── script.js       # Frontend JavaScript
└── templates/
    └── index.html      # Main chat interface
```

## 🎨 UI Features

### Chat Interface

- Dark theme with modern design
- Chat history sidebar with memory management
- Text-to-speech toggle
- Responsive design for mobile devices
- Typing animations for AI responses

### Memory Management

- Create new chat sessions
- Rename chat conversations
- Delete individual chats
- Clear all chat history
- Persistent chat storage

## 🔧 How It Works

### Chat Flow

1. **User Input**: Type your message in the input field
2. **AI Processing**: Message sent to Gemini AI API
3. **Response Generation**: AI generates response
4. **Display**: Response shown with typing animation
5. **Storage**: Conversation saved to chat memory

### Features

- **Real-time Chat**: Instant responses from Gemini AI
- **Memory System**: Persistent chat history
- **Text-to-Speech**: Optional voice output
- **Mobile Responsive**: Works on all devices

## 🛠️ Customization

### Styling

- Modify `static/style.css` for interface styling
- Colors and themes can be easily adjusted
- Responsive breakpoints for mobile optimization

### Chat Behavior

- Adjust typing animation speed in `static/script.js`
- Modify TTS settings for voice output
- Customize chat memory storage

## 🐛 Troubleshooting

### Chat Issues

1. Verify Gemini API key is valid
2. Check internet connection
3. Review browser console for errors
4. Ensure API key is properly set in `.env`

### Common Issues

- **API Key Error**: Make sure your Gemini API key is correct
- **No Response**: Check your internet connection
- **Styling Issues**: Clear browser cache

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

**Enjoy chatting with AI! 🤖✨**
