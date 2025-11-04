# hospital_agent.py
from langgraph.graph import StateGraph
from langgraph.nodes import ToolNode, RouterNode, FunctionNode
from langchain_openai import ChatOpenAI
import requests

# ---- Define Tools (functions) ----
def get_doctor_info(query):
    """Fetch doctor info from FastAPI backend"""
    res = requests.get("http://localhost:8000/doctors")
    return res.json()

def book_appointment(doctor_id, patient_name, start_datetime):
    """Book appointment using FastAPI endpoint"""
    payload = {
        "doctor_id": doctor_id,
        "patient_name": patient_name,
        "start_datetime": start_datetime
    }
    res = requests.post("http://localhost:8000/appointments", json=payload)
    return res.json()

def recommend_doctor(symptoms):
    """Simple logic to recommend a doctor based on symptoms"""
    if "heart" in symptoms.lower():
        return "You should consult a cardiologist."
    elif "fever" in symptoms.lower() or "cold" in symptoms.lower():
        return "You should see a general physician."
    return "Please describe your symptoms in more detail."
