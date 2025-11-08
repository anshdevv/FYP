import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.config import supabase, GOOGLE_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI

# === Initialize ===
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api=GOOGLE_API_KEY)
PKT = ZoneInfo("Asia/Karachi")

class BookAppointment:
    def __call__(self, state):

        user_input = state.get("user_input", "")
        patient_id = state.get("patient_id", 1)

        # --- Step 1: Extract details using LLM ---
        prompt = f"""
        You are a structured information extractor for a hospital chatbot.
        From the user's message: "{user_input}"
        Extract JSON with:
        {{
          "doctor_name": "doctor's name or null if not mentioned",
          "specialization": "probable specialization (e.g. cardiologist, orthopedic, dentist)",
          "date": "YYYY/MM/DD format; if you get proper date then write date else write 'tomorrow' or weekdays like 'next Monday' or whatever the user said",
          "time": "24-hour format; morning=09:00, afternoon=14:00, evening=18:00"
        }}
        Return ONLY valid JSON, no explanations.
        """

        result = llm.invoke(prompt)
        raw_output = getattr(result, "content", str(result))

        clean_json = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not clean_json:
            state["response"] = "Sorry, I couldn’t understand your message. Could you rephrase?"
            return state
        data = json.loads(clean_json.group())

        doctor_name = data.get("doctor_name")
        specialization = data.get("specialization")

        date = data.get("date")
        time = data.get("time")
        user_date_str = data.get("date")  # This is what LLM returned as string
        print(user_date_str)
        print(data)

        now = datetime.now(PKT)  # current time in PKT

        if not user_date_str:
            state["response"] = "Please provide a valid date."
            return state

        # Handle relative terms
        if "tomorrow" in user_date_str.lower():
            target_date = now + timedelta(days=1)
        elif "day after tomorrow" in user_date_str.lower():
            target_date = now + timedelta(days=2)
        else:
            try:
                target_date = datetime.strptime(user_date_str, "%Y/%m/%d")
            except ValueError:
                state["response"] = "Please provide a valid date in YYYY/MM/DD format."
                return state

        # Format for PKT / database
        date = target_date.strftime("%Y/%m/%d")
        weekday =weekday_map[target_date.strftime("%A")]
        print(weekday)



        # --- Step 3: Missing details check ---
        if not time or not date:
            state["response"] = "Please provide a valid date and time for the appointment."
            return state

        # --- Step 4: If doctor not mentioned, suggest based on specialization ---
        if not doctor_name:
            if not specialization:
                state["response"] = "Please mention the doctor or your health concern (e.g., skin issue, bones, heart)."
                return state

# Step 1: Get doctors by specialization
            doctors_res = (
                supabase.table("Doctors")
                .select()
                .ilike("Specialization", f"%{specialization}%")
                .execute()
            )

            if not doctors_res.data:
                state["response"] = f"No doctors found for specialization '{specialization}'."
                return state

            # Step 2: If date and time are given, filter by availability
            available_doctors = []

            if date and time:
                # Convert date string to weekday
                target_date = datetime.strptime(date, "%Y/%m/%d")
                weekday = target_date.strftime("%A")

                for doc in doctors_res.data:
                    avail_res = (
                        supabase.table("doctor_availability")
                        .select("*")
                        .eq("doctor_id", doc["id"])
                        .filter('days', 'ilike', '%Sun%') # Case-insensitive
                        .execute()
                    )
                    # Skip doctors with no availability that day
                    if not avail_res.data:
                        continue

                    # Check if requested time falls in any available slot
                    for slot in avail_res.data:
                        if slot["start_time"] <= time <= slot["end_time"]:
                            available_doctors.append(doc)
                            break
            else:
                # If date or time missing, include all doctors
                available_doctors = doctors_res.data

            if not available_doctors:
                state["response"] = f"No {specialization} doctors are available on {date} at {time}."
                return state

            # Step 3: Prepare response
            doctor_list = "\n".join([
                f"- Dr. {d['Name']} ({d['Experience']} yrs exp)" for d in available_doctors
            ])

            state["response"] = (
                f"Available {specialization} doctors"
                + (f" for {date} at {time}" if date and time else "")
                + f":\n{doctor_list}\n\nPlease tell me which doctor you’d like to book an appointment with."
            )

            # Temporarily store candidate doctors
            # state["candidate_doctors"] = doctor_res.data
            return state

        # --- Step 5: Lookup doctor ---
        doctor_res = supabase.table("Doctors").select("id, Name").ilike("Name", f"%{doctor_name}%").execute()
        if not doctor_res.data:
            state["response"] = f"Doctor '{doctor_name}' not found."
            return state

        doctor = doctor_res.data[0]
        doctor_id = doctor["id"]

        # --- Step 6: Check availability ---
        weekday = datetime.strptime(date, "%Y/%m/%d").strftime("%A")
        avail = (
            supabase.table("doctor_availability")
            .select("*")
            .eq("doctor_id", doctor_id)
            .eq("days", weekday)
            .execute()
        )

        if not avail.data:
            state["response"] = f"{doctor['Name']} is not available on {weekday}."
            return state

        slot = avail.data[0]
        if not (slot["start_time"] <= time <= slot["end_time"]):
            state["response"] = f"{doctor['Name']} is not available at {time}. Please choose another time."
            return state

        # --- Step 7: Book appointment ---
        appointment = {
            "created_At": datetime.now(PKT).isoformat(),
            "patient_id": patient_id,
            "appt date": date,
            "time": time,
            "docotr_id": doctor_id,
        }
        supabase.table("appointments").insert(appointment).execute()

        state["response"] = (
            f"✅ Appointment booked successfully!\n"
            f"Doctor: {doctor['Name']}\nDate: {date}\nTime: {time} (PKT)"
        )
        return state
