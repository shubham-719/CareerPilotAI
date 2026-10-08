from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from ..services.ai_service import get_llm


class RouterState(TypedDict):
    user_message: str
    intent: str


def route_career_request(state: RouterState):
    """
    Analyze the user's message and determine
    which CareerPilot agent should handle it.
    """

    llm = get_llm()

    prompt = f"""
You are the routing system for CareerPilot AI.

Analyze the user's request and classify it into exactly ONE
of the following categories:

- resume
- jobs
- interview
- career
- general

Category definitions:

resume:
Questions about resume, CV, ATS, resume improvement,
resume analysis, skills in resume, or resume writing.

jobs:
Questions about finding jobs, job search, job matching,
companies, job applications, job opportunities, or vacancies.

interview:
Questions about interview preparation, mock interviews,
technical interviews, HR interviews, interview questions,
or interview practice.

career:
Questions about career planning, learning roadmaps,
skill development, career transition, or what to learn next.

general:
Anything that does not clearly belong to the categories above.

User request:
{state["user_message"]}

Return ONLY the category name.

Do not return explanations.
Do not return markdown.
Do not return multiple categories.
"""

    response = llm.invoke(prompt)

    if isinstance(response.content, str):
        intent = response.content.strip().lower()

    elif isinstance(response.content, list):
        text_parts = []

        for item in response.content:
            if isinstance(item, dict):
                text = item.get("text")

                if text:
                    text_parts.append(text)

            elif isinstance(item, str):
                text_parts.append(item)

        intent = "".join(text_parts).strip().lower()

    else:
        intent = str(response.content).strip().lower()

    valid_intents = {
        "resume",
        "jobs",
        "interview",
        "career",
        "general"
    }

    if intent not in valid_intents:
        intent = "general"

    return {
        "intent": intent
    }


def build_router_agent():
    """
    Build the CareerPilot router workflow.
    """

    workflow = StateGraph(RouterState)

    workflow.add_node(
        "router",
        route_career_request
    )

    workflow.add_edge(
        START,
        "router"
    )

    workflow.add_edge(
        "router",
        END
    )

    return workflow.compile()


router_graph = build_router_agent()