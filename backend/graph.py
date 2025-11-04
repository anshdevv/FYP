from langgraph.graph import StateGraph, END
from typing import TypedDict

from .nodes import (
    classify_intent,
    extract_details,
    info_node,
    booking_node,
    recommendation_node,
    general_chat_node,
)


# Define the conversation state schema
class ChatState(TypedDict, total=False):
    user_input: str
    intent: str
    response: str
    doctor_name: str
    specialty: str
    date: str
    time: str


def create_graph():
    # Create the graph
    graph = StateGraph(ChatState)

    # Add nodes
    graph.add_node("classify_intent", classify_intent)
    # graph.add_node("extract_details", extract_details)
    graph.add_node("info", info_node)
    graph.add_node("booking", booking_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("general_chat", general_chat_node)

    # Set the starting point
    graph.set_entry_point("classify_intent")

    # Conditional routing after intent classification
    def route_intent(state):
        intent = state.get("intent", "").lower()
        if intent in ["get_info", "book_appointment", "get_recommendation"]:
            return intent
        else:
            return "general"
        
    

    graph.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "get_info": "info",
            "book_appointment": "booking",
            "get_recommendation": "recommendation",
            "general": "general_chat",
        },
    )

    # # Conditional routing after extracting details
    # def route_after_details(state):
    #     if state.get("intent") == "get_info":
    #         return "info"
    #     elif state.get("intent") == "book_appointment":
    #         return "booking"
    #     return "general_chat"

    # graph.add_conditional_edges(
    #     "extract_details",
    #     route_after_details,
    #     {
    #         "get_info": "info",
    #         "book_appointment": "booking",
    #         "general_chat": "general_chat",
    #     },
    # )

    # End nodes
    for node in ["info", "booking", "recommendation", "general_chat"]:
        graph.add_edge(node, END)

    return graph
