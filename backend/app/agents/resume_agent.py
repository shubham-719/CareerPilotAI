from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from ..services.ai_service import get_llm


class ResumeAgentState(TypedDict):
    user_message: str
    response: str


def resume_agent(state: ResumeAgentState):
    """
    Analyze and improve resumes based on the user's request.
    """

    llm = get_llm()

    prompt = f"""
You are CareerPilot AI's Resume Specialist Agent.

Your responsibility is to help users with:

- Resume improvement
- CV writing
- ATS optimization
- Resume analysis
- Resume formatting
- Professional summaries
- Skills section improvement
- Project descriptions
- Experience bullet points
- Resume tailoring for specific jobs

User request:
{state["user_message"]}

Provide a practical and professional response.

If the user asks for resume improvements:
- Identify weak areas.
- Suggest stronger wording.
- Use professional action verbs.
- Keep claims truthful.
- Optimize content for ATS when appropriate.
- Prefer measurable impact when the user provides real numbers.
- Do not invent experience, skills, companies, achievements, or qualifications.

Use clear headings and bullet points where useful.

Return only the final response for the user.
"""

    response = llm.invoke(prompt)

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


def build_resume_agent():
    """
    Build the Resume Agent workflow.
    """

    workflow = StateGraph(ResumeAgentState)

    workflow.add_node(
        "resume_agent",
        resume_agent
    )

    workflow.add_edge(
        START,
        "resume_agent"
    )

    workflow.add_edge(
        "resume_agent",
        END
    )

    return workflow.compile()


resume_graph = build_resume_agent()