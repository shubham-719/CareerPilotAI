from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from .router_agent import route_career_request
from .career_agent import career_agent
from .resume_agent import resume_agent
from .job_agent import job_agent
from .interview_agent import interview_agent


class MasterAgentState(TypedDict):
    user_message: str
    intent: str
    response: str


def router_node(state: MasterAgentState):
    """
    Use the Router Agent to classify the user's request.
    """

    result = route_career_request(
        {
            "user_message": state["user_message"],
            "intent": ""
        }
    )

    return {
        "intent": result["intent"]
    }


def career_node(state: MasterAgentState):
    """
    Run the Career Agent directly.
    """

    result = career_agent(
        {
            "user_message": state["user_message"],
            "response": ""
        }
    )

    return {
        "response": result["response"]
    }


def resume_node(state: MasterAgentState):
    """
    Run the Resume Agent directly.
    """

    result = resume_agent(
        {
            "user_message": state["user_message"],
            "response": ""
        }
    )

    return {
        "response": result["response"]
    }


def job_node(state: MasterAgentState):
    """
    Run the Job Agent directly.
    """

    result = job_agent(
        {
            "user_message": state["user_message"],
            "response": ""
        }
    )

    return {
        "response": result["response"]
    }


def interview_node(state: MasterAgentState):
    """
    Run the Interview Agent directly.
    """

    result = interview_agent(
        {
            "user_message": state["user_message"],
            "response": ""
        }
    )

    return {
        "response": result["response"]
    }


def route_to_agent(state: MasterAgentState):
    """
    Select the appropriate specialized agent
    based on the router's intent.
    """

    intent = state["intent"]

    if intent == "resume":
        return "resume"

    if intent == "jobs":
        return "jobs"

    if intent == "interview":
        return "interview"

    if intent == "career":
        return "career"

    # General requests use Career Agent as fallback.
    return "career"


def build_master_graph():
    """
    Build the complete CareerPilot multi-agent workflow.
    """

    workflow = StateGraph(MasterAgentState)

    # Router
    workflow.add_node(
        "router",
        router_node
    )

    # Specialized agents
    workflow.add_node(
        "resume",
        resume_node
    )

    workflow.add_node(
        "jobs",
        job_node
    )

    workflow.add_node(
        "interview",
        interview_node
    )

    workflow.add_node(
        "career",
        career_node
    )

    # START → Router
    workflow.add_edge(
        START,
        "router"
    )

    # Router → Correct Agent
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "resume": "resume",
            "jobs": "jobs",
            "interview": "interview",
            "career": "career"
        }
    )

    # Agents → END
    workflow.add_edge(
        "resume",
        END
    )

    workflow.add_edge(
        "jobs",
        END
    )

    workflow.add_edge(
        "interview",
        END
    )

    workflow.add_edge(
        "career",
        END
    )

    return workflow.compile()


master_graph = build_master_graph()