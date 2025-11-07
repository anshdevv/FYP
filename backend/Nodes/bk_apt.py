class BookAppointment:
    def __call__(self, state):
        state["response"] = "Your appointment has been booked successfully."
        return state
