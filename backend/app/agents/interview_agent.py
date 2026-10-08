from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from ..services.ai_service import get_llm


class InterviewAgentState(TypedDict):
    user_message: str
    response: str


def extract_response_text(response) -> str:
    """
    Extract plain text from a LangChain AIMessage.
    Handles different Gemini/LangChain response formats.
    """

    # ---------------------------------------------
    # 1. Try response.text
    # ---------------------------------------------

    try:
        text = response.text

        if isinstance(text, str) and text.strip():
            return text.strip()

    except Exception:
        pass

    # ---------------------------------------------
    # 2. Read response.content
    # ---------------------------------------------

    content = getattr(response, "content", None)

    if isinstance(content, str):
        return content.strip()

    # ---------------------------------------------
    # 3. Handle list-based Gemini content
    # ---------------------------------------------

    if isinstance(content, list):

        text_parts = []

        for item in content:

            # Example:
            # "Some response text"
            if isinstance(item, str):
                text_parts.append(item)
                continue

            # Example:
            # {"type": "text", "text": "..."}
            if isinstance(item, dict):

                text = item.get("text")

                if text:
                    text_parts.append(str(text))

                continue

            # -----------------------------------------
            # Handle object-style content blocks
            # -----------------------------------------

            try:
                text = getattr(item, "text", None)

                if text:
                    text_parts.append(str(text))

            except Exception:
                pass

        if text_parts:
            return "\n".join(text_parts).strip()

    # ---------------------------------------------
    # 4. Fallback string conversion
    # ---------------------------------------------

    try:
        fallback = str(response)

        if fallback and fallback != "None":
            return fallback.strip()

    except Exception:
        pass

    return ""


def interview_agent(state: InterviewAgentState):
    """
    Interview Preparation Specialist Agent.
    """

    llm = get_llm()

    prompt = f"""
You are CareerPilot AI's Interview Preparation Specialist Agent.

Your responsibility is to help users with:

- Technical interview preparation
- Python interview questions
- SQL interview questions
- React and frontend interview questions
- Backend interview questions
- HR interview preparation
- Behavioral interview questions
- Mock interviews
- Interview answer improvement
- Coding interview preparation
- Interview strategies
- Fresher interview preparation

User request:
{state["user_message"]}

Provide a practical and professional response.

Important rules:

1. If the user asks for interview questions:
   - Provide exactly the requested number when possible.
   - Give a clear answer for every question.
   - Explain technical concepts simply.
   - Include short examples where useful.
   - Keep the difficulty appropriate for a fresher.

2. If the user asks for a mock interview:
   - Ask one interview question at a time.
   - Wait for the user's answer before asking the next question.

3. If the user provides an interview answer for review:
   - Evaluate clarity.
   - Evaluate technical correctness.
   - Evaluate structure.
   - Evaluate professional communication.
   - Suggest improvements.

4. Do not invent the user's experience,
   projects, achievements, or skills.

5. For HR questions, provide authentic answer frameworks.

Use clear headings and bullet points where useful.

Return only the final answer for the user.
"""

    response = llm.invoke(prompt)

    response_text = extract_response_text(response)

    if not response_text:
        response_text = (
            "Interview Agent received an empty response from Gemini."
        )

    return {
        "response": response_text
    }


def build_interview_agent():
    workflow = StateGraph(InterviewAgentState)

    workflow.add_node(
        "interview_agent",
        interview_agent
    )

    workflow.add_edge(
        START,
        "interview_agent"
    )

    workflow.add_edge(
        "interview_agent",
        END
    )

    return workflow.compile()


interview_graph = build_interview_agent()