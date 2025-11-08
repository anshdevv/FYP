from langchain_google_genai import ChatGoogleGenerativeAI
from ..config import GOOGLE_API_KEY
from .general import GeneralQuery
from .rec_doc import RecommendDoctor
from .bk_apt import BookAppointment

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api=GOOGLE_API_KEY)

class IntentClassifier:
    def __call__(self, state):
        user_input = state.get("user_input", "")

        # Ask Gemini explicitly for the intent
        prompt = f"""
You are an intent classifier for a hospital chatbot.

Your job:
1. Classify the user's intent into one of these categories:
   - "book_appointment"
   - "recommend_doctor"
   - "general_query"

2. If the user is describing symptoms (e.g., pain, fever, rash, etc.),
   set intent = "general_query" and include a probable doctor specialization
   (e.g., "dentist", "cardiologist", "dermatologist", "ENT", "general physician").

3. If the user wants to book an appointment, extract:
   - The doctor's name (if mentioned)
   - The preferred date and/or time (if mentioned)
4. If the users asks for docotrs regarding a particular specialization or name of a human being and mention doctor then set the intent to recommend_doctor

5."date": "YYYY/MM/DD format; if you get proper date then write date else write 'tomorrow' or weekdays like 'next Monday' or whatever the user said",
"time": "24-hour format; morning=09:00, afternoon=14:00, evening=18:00"
Important:
- Return **only valid JSON** exactly in this format:
Format:
'
  "intent": " ",
  "specialization": " ",
  "doctor_name": " ",
  "date": " ",
  "time": " "
- Use empty strings "" for any information not provided.
- Do NOT include any text outside the JSON. No explanations, notes, or quotes.

User: "{user_input}"
Return the JSON only.

        """
        response = llm.invoke(prompt)
        response = response.content.strip().lower()
        import json
        import re

        # Remove code block markers and leading/trailing whitespace
        clean_response = re.search(r"\{.*\}", response, re.DOTALL)
        if clean_response:
            clean_response = clean_response.group(0)
        else:
            print("failed cleaning json")

        # print(clean_response)
        result = json.loads(clean_response)

        intent = result["intent"]
        specialization = result.get("specialization")
        date= result.get("date")
        time = result.get("time")

        state["intent"] = intent
        state["specialization"] = specialization
        state["date"] = date
        state["time"] = time
        state["doctor_name"]=result.get("doctor_name")
        


        if intent=="general_query":
            print("inside general query")
            state = GeneralQuery()(state)

        elif intent=="recommend_doctor":
            state = RecommendDoctor()(state)

        elif intent=="book_appointment":
            state = BookAppointment()(state)
        
        # state["intent"] = intent
        return state
