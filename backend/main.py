import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse


# ✅ Load environment variables from .env first (before imports that need them)
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .graph import create_graph

# Initialize FastAPI app
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = create_graph().compile()


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    result = graph.invoke({"user_input": user_message})
    print(result)
    return JSONResponse({"response": result.get("response", "No response.")})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
