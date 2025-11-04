from .config import supabase
from datetime import datetime, timedelta
import dateparser
from typing import Optional, Dict, Any

# Helper: normalize common date words into ISO date (YYYY-MM-DD)
def normalize_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    parsed = dateparser.parse(date_str, settings={"PREFER_DATES_FROM": "future"})
    if not parsed:
        return date_str
    return parsed.date().isoformat()

# Helper: normalize time into HH:MM (24h)
def normalize_time(time_str: Optional[str]) -> Optional[str]:
    if not time_str:
        return None
    parsed = dateparser.parse(time_str)
    if not parsed:
        return time_str
    return parsed.time().strftime("%H:%M")

# --- Tools that interact with Supabase ---

def get_doctor_info(specialization: Optional[str] = None,
                    doctor_name: Optional[str] = None,
                    date: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns list of doctors, optionally filtered by specialization or name.
    If date is provided, this function will include doctors that have any availability
    on that day if the doctors table contains an `available_slots` jsonb column.
    """
    q = supabase.table("doctors").select("*")
    if specialization:
        q = q.ilike("specialization", f"%{specialization}%")
    if doctor_name:
        q = q.ilike("name", f"%{doctor_name}%")
    res = q.execute()
    doctors = res.data or []

    # If date filtering is desired and available_slots is present,
    # try to filter by weekday key present in available_slots.
    if date:
        iso_date = normalize_date(date)
        try:
            dt = datetime.fromisoformat(iso_date)
            weekday = dt.strftime("%a").lower()  # e.g. 'mon', 'tue'
        except Exception:
            weekday = None

        if weekday:
            filtered = []
            for d in doctors:
                slots = d.get("available_slots") or {}
                # slots could be like {"mon": ["10:00-13:00"], "tue": ["14:00-15:00"]}
                if isinstance(slots, dict):
                    # check any key match ignoring case
                    keys = {k.lower(): v for k, v in slots.items()}
                    if keys.get(weekday):
                        filtered.append(d)
                else:
                    # if no structured slots, keep the doctor (conservative)
                    filtered.append(d)
            doctors = filtered

    return {"doctors": doctors}

def book_appointment(doctor_id: int, patient_name: str, date: str, time: str) -> Dict[str, Any]:
    """
    Insert appointment record into Supabase.
    `date` expected as natural language / ISO; `time` as natural language or HH:MM.
    Function normalizes and inserts start_datetime.
    """
    iso_date = normalize_date(date)
    iso_time = normalize_time(time)

    if not iso_date or not iso_time:
        return {"error": "Could not parse date/time. Please provide clearer date and time."}

    # combine into ISO datetime
    start_iso = f"{iso_date}T{iso_time}:00"
    try:
        # Ensure valid parse
        dt = datetime.fromisoformat(start_iso)
    except Exception:
        return {"error": "Invalid date/time combination."}

    payload = {
        "doctor_id": doctor_id,
        "patient_name": patient_name,
        "start_datetime": dt.isoformat()
    }
    res = supabase.table("appointments").insert(payload).execute()
    if res.error:
        return {"error": str(res.error)}
    return {"appointment": res.data}

def recommend_doctor_with_llm(
        specialization_hint: Optional[str], 
        symptoms: str, llm) -> str:
    """
    Use LLM to triage symptoms into a recommended specialization string.
    This function expects an instantiated llm object compatible with LangChain's chat interface.
    Returns a short text recommendation.
    """
    prompt = f"""
You are a medical triage assistant (non-diagnostic). A patient reports these symptoms:

\"\"\"{symptoms}\"\"\"

If the user already specified a specialization or doctor (hint: {specialization_hint}), prefer matching recommendations.
Return one short sentence recommending the doctor specialization and a brief reason. Example: "You should consult a Cardiologist because of chest pain and shortness of breath."
"""
    # the llm variable will likely be a LangChain Chat model with .generate or .predict — we will call `.generate` or `.invoke` from nodes.py
    response = llm.invoke(prompt)
    # ✅ Return only the text content (string)
    return response.content if hasattr(response, "content") else str(response)
