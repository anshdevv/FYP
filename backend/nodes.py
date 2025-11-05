from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import PromptTemplate as ChatPromptTemplate
from .tools import get_doctor_info, book_appointment, recommend_doctor_with_llm
from .config import GEMINI_API_KEY
import dotenv
import os
dotenv.load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
)

def classify_intent(state):
    # Same as before, but store intent in context/session
    prompt = ChatPromptTemplate.from_template(
        "User said: {user_input}\n"
        "Classify the intent as one of:\n"
        "1. get_info - asking about doctors, departments, or facilities\n"
        "2. book_appointment - request to schedule with a doctor\n"
        "3. get_recommendation - describe symptoms for advice\n"
        "4. general - greetings, thanks, small talk\n"
        "Return ONLY the keyword."
    )
    chain = prompt | llm
    response = chain.invoke({"user_input": state["user_input"]})
    state["intent"] = response.content.strip().lower()
    return state

def extract_details(state):
# def extract_details(state):
    user_input = state["user_input"].lower()
    state["specialty"] = "dentist" if "dentist" in user_input else ""
    state["date"] = "tomorrow" if "tomorrow" in user_input else ""
    state["time"] = "morning" if "morning" in user_input else ""
    # Also check for "appointment", doctor names, etc.
    return state

def info_node(state):
    context = state.get("user_context", {})
    # Use context for followup questions
    prompt = f"""
    You are a friendly hospital assistant.
    User asked: "{state.get('user_input')}"
    Context: {context}
    Respond empathetically and ask if they need further help.
    """
    response = llm.invoke(prompt).content
    state["response"] = response
    return state

def booking_node(state):
    doc_name = state.get("doctor_name", "")
    specialty = state.get("specialty", "")
    date = state.get("date", "")
    time = state.get("time", "")
    prompt = (
        f"You are a friendly hospital assistant. The user wants to book an appointment.\n"
        f"Specialty: {specialty or doc_name}\n"
        f"Date: {date}\nTime: {time}\n"
        "If any information is missing, ask for it specifically. If all is present, confirm the booking."
    )
    response = llm.invoke(prompt).content
    state["response"] = response
    return state

def recommendation_node(state):
    context = state.get("user_context", {})
    prompt = f"""
    You are an empathetic triage assistant.
    User's symptoms so far: "{state.get('user_input')}". Use previous history: {context.get('history')}
    Suggest which specialist or doctor they might consult, reassure, and ask if they'd like to book.
    """
    response = llm.invoke(prompt).content
    state["response"] = response
    return state

def general_chat_node(state):
    context = state.get("user_context", {})
    prompt = f"""
    You are a warm, helpful hospital chatbot assistant.
    Remember prior exchanges (history: {context.get('history')}).
    If the user greets, share a friendly welcome and ask how you can help.
    Keep the tone caring and conversational.
    """
    response = llm.invoke(prompt).content
    state["response"] = response
    return state