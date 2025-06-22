# Gemini Pro Chatbot with FastAPI

This project is a simple AI chatbot that uses the Gemini Pro API and is served with a FastAPI backend.

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create a virtual environment

It's recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

Create a `.env` file in the root of the project and add your Gemini API key:

```
GEMINI_API_KEY=Your_Key
```

**Note:** Replace `Your_key` with your actual Gemini API key.

## How to Run

1.  **Start the FastAPI server:**

    Use `uvicorn` to run the server:

    ```bash
    uvicorn main:app --reload
    ```

    The `--reload` flag automatically restarts the server when you make changes to the code.

2.  **Access the API:**

    The API will be available at `http://127.0.0.1:8000`.

## Usage

You can interact with the chatbot by sending a POST request to the `/chat` endpoint.

### Example using `curl`

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
-H "Content-Type: application/json" \
-d '{"message": "Hello, how are you?"}'
```

### Expected Response

The API will return a JSON object with the AI's response:

```json
{
  "response": "I am doing well, thank you for asking! How can I help you today?"
}
```
