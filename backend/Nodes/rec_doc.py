from backend.config import supabase
from datetime import datetime
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class RecommendDoctor:
    def __call__(self, state):

        user_input = state.get("user_input", "").lower()
        PKT = ZoneInfo("Asia/Karachi")

        specialization = state.get("specialization")
        date = state.get("date")  # Expected format: YYYY/MM/DD
        time = state.get("time") 

        user_date_str =state.get("date") # This is what LLM returned as string

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
        weekday = target_date.strftime("%a") # Expected format: HH:MM (24-hour)

        if not specialization:
            state["response"] = "Please specify the specialization you are looking for."
            return state

        try:
            # === Step 1: Get doctors by specialization ===
            doctors_res = (
                supabase.table("Doctors")
                .select("*")
                .ilike("Specialization", f"%{specialization}%")
                .execute()
            )

            if not doctors_res.data:
                state["response"] = f"Sorry, I couldn’t find any available {specialization}s right now."
                return state

            # === Step 2: Filter by availability if date and time are provided ===
            available_doctors = []
            print(weekday)
            print(date)
            print(time)

            if date and time:
                try:
                    target_date = datetime.strptime(date, "%Y/%m/%d")
                    weekday = target_date.strftime("%A")
                except ValueError:
                    state["response"] = "Invalid date format. Please use YYYY/MM/DD."
                    return state
                
                print(doctors_res.data)

                for doc in doctors_res.data:
                    avail_res = (
                        supabase.table("doctor_availability")
                        .select("*")
                        .eq("doctor_id", doc["id"])
                        .text_search('days', "'Sun'") 
                        # .ilike('days', f'%{weekday}%')  # Case-insensitive

                        .execute()
                    )
                    available_doctors.append(doc)


                    if not avail_res.data:
                        # print("no avail res")
                        continue

                    # Check if requested time falls within any available slot
                    for doc in avail_res.data:
                        print(doc["start_time"], time, doc["end_time"])
                        if doc["start_time"] <= time <= doc["end_time"]:
                            available_doctors.append(doc)
                            break
            else:
                # If no date/time, include all doctors
                available_doctors = doctors_res.data

            if not available_doctors:
                state["response"] = (
                    f"No {specialization} doctors are available"
                    + (f" on {date} at {time}" if date and time else "")
                    + "."
                )
                return state

            # === Step 3: Prepare response ===
            doctor_list = "\n".join([
                f"- Dr. {d['Name']} ({d.get('Qualification', 'N/A')}, {d.get('Experience', 0)} yrs exp, Room {d.get('room', 'N/A')})"
                for d in available_doctors
            ])

            state["response"] = (
                f"I recommend consulting a {specialization}.\n"
                f"Here are some available doctors"
                + (f" on {date} at {time}" if date and time else "")
                + f":\n{doctor_list}\n"
                f"Would you like to book an appointment with one?"
            )

        except Exception as e:
            state["response"] = f"Error fetching doctor data: {e}"

        return state
