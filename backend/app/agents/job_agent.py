from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from ..services.ai_service import get_llm


class JobAgentState(TypedDict):
    user_message: str
    response: str


def job_agent(state: JobAgentState):
    """
    Help users with job search, job matching,
    job applications, and job-search strategy.
    """

    llm = get_llm()

    prompt = f"""
You are CareerPilot AI's Job Search Specialist Agent.

Your responsibility is to help users with:

- Job search strategies
- Job matching
- Job role recommendations
- Company research guidance
- Job application strategies
- Job descriptions
- Skill requirements
- Job eligibility
- Career opportunities
- Fresher job guidance
- Software developer job searches

User request:
{state["user_message"]}

Provide a practical and professional response.

Important rules:

1. Do not claim that you searched the internet unless an actual
   search tool was used.

2. Do not invent job openings, companies, salaries, application
   deadlines, or job URLs.

3. If the user asks for current job openings but no search tool
   is available, explain that current listings cannot be verified
   and provide a useful job-search strategy instead.

4. If the user asks whether they are suitable for a role, compare
   their stated skills with the requirements they provide.

5. When recommending job roles, explain:
   - Recommended role
   - Required skills
   - Why the role fits
   - Skills to improve
   - Suggested next steps

6. Keep the response structured and easy to understand.

Use headings and bullet points where useful.

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


def build_job_agent():
    """
    Build the Job Search Agent workflow.
    """

    workflow = StateGraph(JobAgentState)

    workflow.add_node(
        "job_agent",
        job_agent
    )

    workflow.add_edge(
        START,
        "job_agent"
    )

    workflow.add_edge(
        "job_agent",
        END
    )

    return workflow.compile()


job_graph = build_job_agent()