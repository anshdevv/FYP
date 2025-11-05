from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.graph import app as graph_app

app = FastAPI()

# In-memory chat history store {session_id: [ {"role": "user"/"bot", "message": "..."} ]}
chat_histories = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")

    # initialize chat if new
    if session_id not in chat_histories:
        chat_histories[session_id] = []

    # store user message
    chat_histories[session_id].append({"role": "user", "message": user_message})

    # get response from graph (send last few messages for context)
    context = "\n".join([f"{m['role']}: {m['message']}" for m in chat_histories[session_id][-6:]])
    result = graph_app.invoke({"input": context})

    bot_reply = result["reply"]
    chat_histories[session_id].append({"role": "bot", "message": bot_reply})

    return JSONResponse({"response": bot_reply, "history": chat_histories[session_id]})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
