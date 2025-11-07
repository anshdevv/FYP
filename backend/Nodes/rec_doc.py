class RecommendDoctor:
    def __call__(self, state):
        state["response"] = "You may consult a general physician. Would you like to book an appointment?"
        return state
