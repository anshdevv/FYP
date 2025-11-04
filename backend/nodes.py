from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import PromptTemplate as ChatPromptTemplate

from .tools import get_doctor_info, book_appointment, recommend_doctor_with_llm
from .config import GEMINI_API_KEY
import dotenv
import os
dotenv.load_dotenv()


print(GEMINI_API_KEY)
# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
)

# ---------- Node 1: Primary Intent ----------
def classify_intent(state):
    """
    Uses the LLM to classify the user's intent.
    """
    prompt = ChatPromptTemplate.from_template(
        "User said: {user_input}\n"
        "Classify the intent as one of:\n"
        "1. get_info - asking for doctor details or specialties\n"
        "2. book_appointment - trying to schedule a consultation\n"
        "3. get_recommendation - asking for advice based on symptoms\n"
        "4. general - for greetings, introductions, or casual talk\n\n"
        "Return ONLY one of these keywords."
    )
    chain = prompt | llm
    response = chain.invoke({"user_input": state["user_input"]})
    intent = response.content.strip().lower()
    state["intent"] = intent
    return state


# ---------- Node 2: Follow-Up Intent / Extract Details ----------
def extract_details(state):
    """
    Extracts doctor name, specialty, date/time from user query if present.
    """
    prompt = ChatPromptTemplate.from_template(
        "User said: {user_input}\n"
        "If user mentioned a specific doctor name, specialty, or date/time, extract them.\n"
        "Return a JSON with keys: doctor_name, specialty, date, time (use null if not found)."
    )
    chain = prompt | llm
    response = chain.invoke({"user_input": state["user_input"]})
    try:
        import json
        details = json.loads(response.content)
        state.update(details)
    except Exception:
        pass
    return state


# ---------- Node 3: Info Node ----------
def info_node(state):
    print("info node called")
    """
    Fetches doctor info filtered by specialty or name.
    """
    doctors = get_doctor_info()
    name = state.get("doctor_name")
    specialty = state.get("specialty")

    if specialty:
        filtered = [d for d in doctors if d["specialty"].lower() == specialty.lower()]
    elif name:
        filtered = [d for d in doctors if d["name"].lower() == name.lower()]
    else:
        filtered = doctors

    state["response"] = filtered
    return state


# ---------- Node 4: Booking Node ----------
def booking_node(state):
    """
    LLM-driven booking assistant.
    Uses the LLM to generate a natural conversation based on the current booking details.
    """
    doc_name = state.get("doctor_name")
    date = state.get("date")
    time = state.get("time")
    patient = state.get("patient_name", "Anonymous")

    doctors = get_doctor_info()
    available_doctors = ", ".join([f"{d['name']} ({d['specialty']})" for d in doctors])

    # Context we pass to LLM
    prompt = f"""
You are a helpful hospital assistant who helps patients book appointments.
Use the following data to reason and respond naturally like a human:

Available doctors: {available_doctors}
User request: "{state.get('user_input')}"
Extracted info:
- Doctor name: {doc_name or "Not provided"}
- Date: {date or "Not provided"}
- Time: {time or "Not provided"}

If doctor name is missing, suggest available doctors.
If time/date is missing, ask politely for missing information.
If all information is provided, confirm booking and say it's been scheduled.

Respond in a short, friendly, natural tone.
"""

    # Invoke the LLM
    response = llm.invoke(prompt).content
    state["response"] = response
    return state


# ---------- Node 5: Recommendation Node ----------
def recommendation_node(state):
    """
    Suggests which doctor/specialty to visit based on symptoms.
    """
    symptoms = state["user_input"]
    state["response"] = recommend_doctor_with_llm(None,symptoms,llm)
    return state


# ---------- Node 6: General Chat (Fallback) ----------
def general_chat_node(state):
    """
    Handles greetings, introductions, or small talk.
    """
    prompt = ChatPromptTemplate.from_template(
        "You are a friendly hospital chatbot assistant.\n"
        "If the user greets or introduces themselves, respond warmly and ask how you can assist.\n"
        "User: {user_input}"
    )
    chain = prompt | llm
    response = chain.invoke({"user_input": state["user_input"]})
    state["response"] = response.content
    return state
