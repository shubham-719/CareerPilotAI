from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from ..services.ai_service import get_llm


class CareerAgentState(TypedDict):
    user_message: str
    response: str


def career_agent(state: CareerAgentState):
    """
    Main CareerPilot AI agent node.
    """

    llm = get_llm()

    prompt = f"""
You are CareerPilot AI, an intelligent career assistant.

User request:
{state["user_message"]}

Your job is to understand the user's career-related request
and provide a useful, clear and practical response.

Focus on:
- Job search
- Resume improvement
- Skills
- Career planning
- Interview preparation
- Learning roadmaps
- Software development careers
- Technical career guidance

Give practical and structured answers.

Use headings and bullet points when useful.

Do not pretend that you performed an action if you did not.

Return only the final answer for the user.
"""

    response = llm.invoke(prompt)

    # Normalize Gemini/LangChain content
    if isinstance(response.content, str):
        response_text = response.content

    elif isinstance(response.content, list):
        text_parts = []

        for item in response.content:
            if isinstance(item, dict):
                text = item.get("text")

                if text:
                    text_parts.append(text)

            elif isinstance(item, str):
                text_parts.append(item)

        response_text = "\n".join(text_parts)

    else:
        response_text = str(response.content)

    return {
        "response": response_text
    }


def build_career_agent():
    """
    Build the LangGraph workflow.
    """

    workflow = StateGraph(CareerAgentState)

    workflow.add_node(
        "career_agent",
        career_agent
    )

    workflow.add_edge(
        START,
        "career_agent"
    )

    workflow.add_edge(
        "career_agent",
        END
    )

    return workflow.compile()


career_graph = build_career_agent()