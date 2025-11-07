class GeneralQuery:
    def __call__(self, state):
        state["response"] = "I can help you with doctor recommendations, appointments, or general hospital info."
        return state
