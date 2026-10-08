from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .models import db, User


auth_api = Blueprint(
    "auth_api",
    __name__,
    url_prefix="/api/auth"
)


@auth_api.route(
    "/register",
    methods=["POST"]
)
def register():
    """
    Register a new CareerPilot user.
    """

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "message": "Request body is required."
        }, 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name:
        return {
            "status": "error",
            "message": "Name is required."
        }, 400

    if not email:
        return {
            "status": "error",
            "message": "Email is required."
        }, 400

    if not password:
        return {
            "status": "error",
            "message": "Password is required."
        }, 400

    name = name.strip()
    email = email.strip().lower()

    if not name:
        return {
            "status": "error",
            "message": "Name cannot be empty."
        }, 400

    if not email:
        return {
            "status": "error",
            "message": "Email cannot be empty."
        }, 400

    if len(password) < 6:
        return {
            "status": "error",
            "message": "Password must be at least 6 characters."
        }, 400

    try:
        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            return {
                "status": "error",
                "message": "An account with this email already exists."
            }, 409

        password_hash = generate_password_hash(
            password
        )

        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )

        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(
            identity=str(user.id)
        )

        return {
            "status": "success",
            "message": "Registration successful.",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            },
            "access_token": access_token
        }, 201

    except Exception as e:

        db.session.rollback()

        return {
            "status": "error",
            "message": "Registration failed.",
            "error": str(e)
        }, 500


@auth_api.route(
    "/login",
    methods=["POST"]
)
def login():
    """
    Authenticate an existing CareerPilot user.
    """

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "message": "Request body is required."
        }, 400

    email = data.get("email")
    password = data.get("password")

    if not email:
        return {
            "status": "error",
            "message": "Email is required."
        }, 400

    if not password:
        return {
            "status": "error",
            "message": "Password is required."
        }, 400

    email = email.strip().lower()

    try:
        user = User.query.filter_by(
            email=email
        ).first()

        if not user:
            return {
                "status": "error",
                "message": "Invalid email or password."
            }, 401

        password_valid = check_password_hash(
            user.password_hash,
            password
        )

        if not password_valid:
            return {
                "status": "error",
                "message": "Invalid email or password."
            }, 401

        access_token = create_access_token(
            identity=str(user.id)
        )

        return {
            "status": "success",
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            },
            "access_token": access_token
        }, 200

    except Exception as e:

        return {
            "status": "error",
            "message": "Login failed.",
            "error": str(e)
        }, 500


@auth_api.route(
    "/me",
    methods=["GET"]
)
@jwt_required()
def current_user():
    """
    Return the currently authenticated user.
    """

    try:
        user_id = get_jwt_identity()

        user = User.query.get(
            int(user_id)
        )

        if not user:
            return {
                "status": "error",
                "message": "User not found."
            }, 404

        return {
            "status": "success",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": (
                    user.created_at.isoformat()
                    if user.created_at
                    else None
                )
            }
        }, 200

    except Exception as e:

        return {
            "status": "error",
            "message": "Failed to load user.",
            "error": str(e)
        }, 500