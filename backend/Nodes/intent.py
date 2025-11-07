class IntentClassifier:
    def __call__(self, state):
        user_input = state.get("user_input", "").lower()

        if any(x in user_input for x in ["book", "appointment", "schedule"]):
            intent = "book_appointment"
        elif any(x in user_input for x in ["pain", "doctor", "recommend", "fever", "consult"]):
            intent = "recommend_doctor"
        else:
            intent = "general_query"

        state["intent"] = intent
        return state
