from fastapi import APIRouter, HTTPException
from app.database import get_connection

import hashlib
import secrets

from app.models.auth import LoginRequest, CreateAgentRequest


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def hash_password(password: str, salt: bytes) -> str:
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100_000
    )

    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, hash_hex = stored_hash.split(":")

    salt = bytes.fromhex(salt_hex)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100_000
    )

    return secrets.compare_digest(
        password_hash.hex(),
        hash_hex
    )


# =========================
# FIELD AGENT LOGIN
# =========================

@router.post("/login")
def login(data: LoginRequest):

    connection = get_connection()

    user = connection.execute(
        """
        SELECT id, username, password_hash, role
        FROM users
        WHERE username = ?
        """,
        (data.username,)
    ).fetchone()

    connection.close()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        data.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    return {
        "success": True,
        "message": "Login successful",
        "username": user["username"],
        "role": user["role"]
    }


# =========================
# ADMIN CREATES FIELD AGENT
# =========================

@router.post("/create-agent")
def create_agent(data: CreateAgentRequest):

    connection = get_connection()

    # Find the admin
    admin = connection.execute(
        """
        SELECT id, password_hash, role
        FROM users
        WHERE username = ?
        """,
        (data.admin_username,)
    ).fetchone()

    # Admin doesn't exist
    if admin is None:
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Invalid admin credentials"
        )

    # Make sure the account is actually an admin
    if admin["role"] != "admin":
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    # Verify admin password
    if not verify_password(
        data.admin_password,
        admin["password_hash"]
    ):
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Invalid admin credentials"
        )

    # Check if username already exists
    existing_user = connection.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        (data.username,)
    ).fetchone()

    if existing_user:
        connection.close()

        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    # Hash the field agent's password
    salt = secrets.token_bytes(16)

    password_hash = hash_password(
        data.password,
        salt
    )

    # Create field agent
    cursor = connection.execute(
        """
        INSERT INTO users (
            username,
            password_hash,
            role
        )
        VALUES (?, ?, ?)
        """,
        (
            data.username,
            password_hash,
            "field_agent"
        )
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "Field agent account created successfully",
        "id": cursor.lastrowid,
        "username": data.username,
        "role": "field_agent"
    }