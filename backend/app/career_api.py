from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from .agents.master_graph import master_graph
from .models import (
    db,
    AgentSession,
    AgentMessage,
    User,
    Resume
)
from .services.resume_service import (
    extract_pdf_text,
    save_resume_file
)


career_api = Blueprint(
    "career_api",
    __name__,
    url_prefix="/api"
)


def get_current_user():
    user_id = get_jwt_identity()

    if not user_id:
        return None

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None

    return User.query.get(user_id)


def get_latest_resume(user_id):
    """
    Return the most recently uploaded resume
    belonging to the authenticated user.
    """

    return Resume.query.filter_by(
        user_id=user_id
    ).order_by(
        Resume.uploaded_at.desc()
    ).first()


def should_attach_resume_context(message):
    """
    Determine whether the user's request is related
    to resume analysis or resume improvement.
    """

    resume_keywords = [
        "resume",
        "cv",
        "ats",
        "analyze my resume",
        "analyse my resume",
        "review my resume",
        "improve my resume",
        "resume analysis",
        "resume review",
        "resume score",
        "ats score",
        "skills from my resume",
        "strengths from my resume",
        "weaknesses from my resume",
        "missing skills",
        "suitable roles",
        "job roles based on my resume",
        "job match"
    ]

    message_lower = message.lower()

    return any(
        keyword in message_lower
        for keyword in resume_keywords
    )


def build_resume_context(resume):
    """
    Build a structured context block for the Resume Agent.
    """

    if not resume:
        return ""

    extracted_text = (
        resume.extracted_text or ""
    ).strip()

    if not extracted_text:
        return ""

    return f"""

============================================================
UPLOADED RESUME CONTEXT
============================================================

The authenticated user has already uploaded a resume.

Resume file name:
{resume.file_name}

Resume ID:
{resume.id}

The following text was extracted directly from the uploaded
PDF resume. Use this information as the primary source for
resume analysis.

IMPORTANT RULES:

1. Analyze the resume below.
2. Do NOT ask the user to paste the resume again.
3. Do NOT claim that the resume was not attached.
4. Do NOT invent experience, skills, projects, education,
   certifications, achievements, or metrics.
5. Preserve factual accuracy.
6. If information is missing, clearly say that it is not
   present in the uploaded resume.
7. For ATS scoring, provide an ESTIMATED score and explain
   the scoring basis.
8. Distinguish clearly between information found in the
   resume and recommendations for improvement.

-------------------- EXTRACTED RESUME --------------------

{extracted_text}

------------------ END EXTRACTED RESUME ------------------

============================================================
END UPLOADED RESUME CONTEXT
============================================================
"""


def create_agent_session(user_id, first_message):
    session = AgentSession(
        user_id=user_id,
        title=first_message[:80],
        status="active"
    )

    db.session.add(session)
    db.session.commit()

    return session


def save_message(
    session_id,
    role,
    content,
    agent_name=None
):
    message = AgentMessage(
        session_id=session_id,
        role=role,
        content=content,
        agent_name=agent_name,
        created_at=datetime.utcnow()
    )

    db.session.add(message)
    db.session.commit()

    return message


@career_api.route(
    "/resume/upload",
    methods=["POST"]
)
@jwt_required()
def upload_resume():
    try:
        user = get_current_user()

        if not user:
            return {
                "status": "error",
                "message": "Authenticated user not found."
            }, 401

        if "resume" not in request.files:
            return {
                "status": "error",
                "message": "Resume PDF is required."
            }, 400

        file = request.files["resume"]

        if not file or not file.filename:
            return {
                "status": "error",
                "message": "Please select a resume PDF."
            }, 400

        original_filename = secure_filename(
            file.filename
        )

        if not original_filename.lower().endswith(".pdf"):
            return {
                "status": "error",
                "message": "Only PDF resume files are allowed."
            }, 400

        saved_path, original_filename = save_resume_file(
            file=file,
            user_id=user.id
        )

        extracted_text = extract_pdf_text(
            saved_path
        )

        if not extracted_text:
            try:
                import os

                if os.path.exists(saved_path):
                    os.remove(saved_path)

            except Exception:
                pass

            return {
                "status": "error",
                "message": (
                    "Could not extract text from the PDF. "
                    "Please upload a text-based PDF resume."
                )
            }, 400

        resume = Resume(
            user_id=user.id,
            file_name=original_filename,
            file_path=saved_path,
            extracted_text=extracted_text
        )

        db.session.add(resume)
        db.session.commit()

        return {
            "status": "success",
            "message": "Resume uploaded successfully.",
            "resume": {
                "id": resume.id,
                "file_name": resume.file_name,
                "uploaded_at": (
                    resume.uploaded_at.isoformat()
                    if resume.uploaded_at
                    else None
                ),
                "text_length": len(
                    extracted_text
                ),
                "preview": extracted_text[:1000]
            }
        }, 201

    except ValueError as e:
        db.session.rollback()

        return {
            "status": "error",
            "message": str(e)
        }, 400

    except Exception as e:
        db.session.rollback()

        return {
            "status": "error",
            "message": "Resume upload failed.",
            "error": str(e)
        }, 500


@career_api.route(
    "/resume",
    methods=["GET"]
)
@jwt_required()
def get_resumes():
    try:
        user = get_current_user()

        if not user:
            return {
                "status": "error",
                "message": "Authenticated user not found."
            }, 401

        resumes = Resume.query.filter_by(
            user_id=user.id
        ).order_by(
            Resume.uploaded_at.desc()
        ).all()

        resume_data = []

        for resume in resumes:
            resume_data.append({
                "id": resume.id,
                "file_name": resume.file_name,
                "uploaded_at": (
                    resume.uploaded_at.isoformat()
                    if resume.uploaded_at
                    else None
                ),
                "text_length": len(
                    resume.extracted_text or ""
                )
            })

        return {
            "status": "success",
            "resumes": resume_data
        }, 200

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to load resumes.",
            "error": str(e)
        }, 500


@career_api.route(
    "/resume/<int:resume_id>",
    methods=["GET"]
)
@jwt_required()
def get_resume(resume_id):
    try:
        user = get_current_user()

        if not user:
            return {
                "status": "error",
                "message": "Authenticated user not found."
            }, 401

        resume = Resume.query.filter_by(
            id=resume_id,
            user_id=user.id
        ).first()

        if not resume:
            return {
                "status": "error",
                "message": "Resume not found."
            }, 404

        return {
            "status": "success",
            "resume": {
                "id": resume.id,
                "file_name": resume.file_name,
                "file_path": resume.file_path,
                "extracted_text": (
                    resume.extracted_text or ""
                ),
                "uploaded_at": (
                    resume.uploaded_at.isoformat()
                    if resume.uploaded_at
                    else None
                )
            }
        }, 200

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to load resume.",
            "error": str(e)
        }, 500


@career_api.route(
    "/resume/<int:resume_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_resume(resume_id):
    try:
        user = get_current_user()

        if not user:
            return {
                "status": "error",
                "message": "Authenticated user not found."
            }, 401

        resume = Resume.query.filter_by(
            id=resume_id,
            user_id=user.id
        ).first()

        if not resume:
            return {
                "status": "error",
                "message": "Resume not found."
            }, 404

        if resume.file_path:
            try:
                import os

                if os.path.exists(
                    resume.file_path
                ):
                    os.remove(
                        resume.file_path
                    )

            except Exception:
                pass

        db.session.delete(resume)
        db.session.commit()

        return {
            "status": "success",
            "message": "Resume deleted successfully.",
            "resume_id": resume_id
        }, 200

    except Exception as e:
        db.session.rollback()

        return {
            "status": "error",
            "message": "Failed to delete resume.",
            "error": str(e)
        }, 500


@career_api.route(
    "/agent/chat",
    methods=["POST"]
)
@jwt_required()
def career_agent_chat():

    data = request.get_json(
        silent=True
    )

    if not data:
        return {
            "status": "error",
            "message": "Request body is required."
        }, 400

    user_message = data.get(
        "message"
    )

    if not user_message:
        return {
            "status": "error",
            "message": "Message is required."
        }, 400

    user_message = user_message.strip()

    if not user_message:
        return {
            "status": "error",
            "message": "Message cannot be empty."
        }, 400

    try:
        user = get_current_user()

        if not user:
            return {
                "status": "error",
                "message": "Authenticated user not found."
            }, 401

        session_id = data.get(
            "session_id"
        )

        session = None

        if session_id:

            try:
                session_id = int(
                    session_id
                )

            except (
                TypeError,
                ValueError
            ):
                return {
                    "status": "error",
                    "message": "Invalid session_id."
                }, 400

            session = AgentSession.query.filter_by(
                id=session_id,
                user_id=user.id
            ).first()

            if not session:
                return {
                    "status": "error",
                    "message": "Chat session not found."
                }, 404

        else:
            session = create_agent_session(
                user.id,
                user_message
            )

        save_message(
            session_id=session.id,
            role="user",
            content=user_message
        )

        # ==================================================
        # RESUME CONTEXT
        # ==================================================

        graph_message = user_message

        if should_attach_resume_context(
            user_message
        ):

            latest_resume = get_latest_resume(
                user.id
            )

            if latest_resume:
                resume_context = build_resume_context(
                    latest_resume
                )

                if resume_context:
                    graph_message = (
                        user_message
                        + "\n\n"
                        + resume_context
                    )

            else:
                graph_message = (
                    user_message
                    + """

IMPORTANT:
The user requested resume-related analysis,
but no uploaded resume was found for this
authenticated account.

Do not pretend that a resume was provided.
Ask the user to upload a resume PDF.
"""
                )

        # ==================================================
        # MASTER GRAPH
        # ==================================================

        result = master_graph.invoke(
            {
                "user_message": graph_message,
                "intent": "",
                "response": ""
            }
        )

        response_text = result.get(
            "response",
            ""
        )

        intent = result.get(
            "intent",
            "general"
        )

        if not response_text:
            db.session.rollback()

            return {
                "status": "error",
                "message": "AI returned an empty response."
            }, 500

        agent_names = {
            "resume": "Resume Agent",
            "jobs": "Job Agent",
            "interview": "Interview Agent",
            "career": "Career Agent",
            "general": "Career Agent"
        }

        agent_name = agent_names.get(
            intent,
            "Career Agent"
        )

        save_message(
            session_id=session.id,
            role="assistant",
            content=response_text,
            agent_name=agent_name
        )

        return {
            "status": "success",
            "session_id": session.id,
            "message": user_message,
            "intent": intent,
            "agent": agent_name,
            "response": response_text
        }, 200

    except Exception as e:
        db.session.rollback()

        return {
            "status": "error",
            "message": "Failed to generate AI response.",
            "error": str(e)
        }, 500


@career_api.route(
    "/agent/sessions",
    methods=["GET"]
)
@jwt_required()
def get_agent_sessions():
    try:
        user = get_current_user()

        if not user:
            return {
                "status": "error",
                "message": "Authenticated user not found."
            }, 401

        sessions = AgentSession.query.filter_by(
            user_id=user.id
        ).order_by(
            AgentSession.created_at.desc()
        ).all()

        session_data = []

        for session in sessions:

            message_count = AgentMessage.query.filter_by(
                session_id=session.id
            ).count()

            session_data.append({
                "id": session.id,
                "title": session.title,
                "status": session.status,
                "message_count": message_count,
                "created_at": (
                    session.created_at.isoformat()
                    if session.created_at
                    else None
                )
            })

        return {
            "status": "success",
            "sessions": session_data
        }, 200

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to load chat sessions.",
            "error": str(e)
        }, 500


@career_api.route(
    "/agent/sessions/<int:session_id>",
    methods=["GET"]
)
@jwt_required()
def get_agent_session(session_id):

    try:
        user = get_current_user()

        if not user:
            return {
                "status": "error",
                "message": "Authenticated user not found."
            }, 401

        session = AgentSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()

        if not session:
            return {
                "status": "error",
                "message": "Chat session not found."
            }, 404

        messages = AgentMessage.query.filter_by(
            session_id=session.id
        ).order_by(
            AgentMessage.created_at.asc()
        ).all()

        message_data = []

        for message in messages:

            message_data.append({
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "agent_name": message.agent_name,
                "created_at": (
                    message.created_at.isoformat()
                    if message.created_at
                    else None
                )
            })

        return {
            "status": "success",
            "session": {
                "id": session.id,
                "title": session.title,
                "status": session.status,
                "created_at": (
                    session.created_at.isoformat()
                    if session.created_at
                    else None
                ),
                "messages": message_data
            }
        }, 200

    except Exception as e:

        return {
            "status": "error",
            "message": "Failed to load chat session.",
            "error": str(e)
        }, 500


@career_api.route(
    "/agent/sessions/<int:session_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_agent_session(session_id):

    try:
        user = get_current_user()

        if not user:
            return {
                "status": "error",
                "message": "Authenticated user not found."
            }, 401

        session = AgentSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()

        if not session:
            return {
                "status": "error",
                "message": "Chat session not found."
            }, 404

        db.session.delete(session)
        db.session.commit()

        return {
            "status": "success",
            "message": "Chat session deleted.",
            "session_id": session_id
        }, 200

    except Exception as e:
        db.session.rollback()

        return {
            "status": "error",
            "message": "Failed to delete chat session.",
            "error": str(e)
        }, 500