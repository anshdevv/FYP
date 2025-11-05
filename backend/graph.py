from langgraph.graph import StateGraph, START
from pydantic import BaseModel
from backend.config import llm  # your LLM from config (e.g., Gemini, OpenAI, etc.)

# --- 1. Define the schema of the conversation state ---
class ChatState(BaseModel):
    input: str
    intent: str | None = None
    reply: str | None = None


# --- 2. Tools or response generators ---
def booking_tool(msg: str):
    return "Sure, I can help you book an appointment. Which doctor or department?"

def info_tool(msg: str):
    return "We have doctors in cardiology, neurology, and pediatrics."

def recommend_tool(msg: str):
    return "Please describe your symptoms, and I’ll suggest the right specialist."


# --- 3. LLM-powered intent classification ---
def classify_intent(state: ChatState):
    msg = state.input
    prompt = f"""
    You are a hospital assistant. Your task is to classify the user's intent 
    into exactly one of the following categories:
    [booking, info, recommend, general].

    Examples:
    - "I want to book an appointment" → booking
    - "Tell me about cardiologists" → info
    - "I have a headache, what should I do?" → recommend
    - "Hi" → general

    User message: "{msg}"

    Respond with only one word — the intent.
    """
    intent = llm.generate_content(prompt).text.strip().lower()
    return ChatState(input=msg, intent=intent)


# --- 4. Handle each intent ---
def handle_intent(state: ChatState):
    msg = state.input
    intent = state.intent or "general"

    if "book" in intent:
        reply = booking_tool(msg)
    elif "info" in intent:
        reply = info_tool(msg)
    elif "recommend" in intent:
        reply = recommend_tool(msg)
    else:
        reply = "Hello! I'm your hospital assistant. How can I help you today?"

    return ChatState(input=msg, intent=intent, reply=reply)


# --- 5. Build and compile the graph ---
graph = StateGraph(ChatState)
graph.add_node("classify_intent", classify_intent)
graph.add_node("handle_intent", handle_intent)

graph.add_edge(START, "classify_intent")
graph.add_edge("classify_intent", "handle_intent")

app = graph.compile()
    
