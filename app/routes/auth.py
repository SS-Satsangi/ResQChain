from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.models.auth import (
    LoginRequest,
    CreateAgentRequest,
    AdminLoginRequest,
    UserUpdateRequest
)

import hashlib
import secrets


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
# ADMIN LOGIN
# =========================

@router.post("/admin-login")
def admin_login(data: AdminLoginRequest):

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
            detail="Invalid admin credentials"
        )

    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    if not verify_password(
        data.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin credentials"
        )

    return {
        "success": True,
        "message": "Admin login successful",
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

# =========================
# GET ALL USERS
# =========================

@router.get("/users")
def get_users():

    connection = get_connection()

    users = connection.execute(
        """
        SELECT id, username, role
        FROM users
        """
    ).fetchall()

    connection.close()

    return {
        "users": [dict(user) for user in users]
    }

# =========================
# EDIT USER
# =========================

@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    admin_username: str,
    admin_password: str
):

    connection = get_connection()

    # Find the admin
    admin = connection.execute(
        """
        SELECT id, password_hash, role
        FROM users
        WHERE username = ?
        """,
        (admin_username,)
    ).fetchone()

    if admin is None:
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Invalid admin credentials"
        )

    # Make sure they are actually an admin
    if admin["role"] != "admin":
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    # Verify admin password
    if not verify_password(
        admin_password,
        admin["password_hash"]
    ):
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Invalid admin credentials"
        )

    # Find target user
    user = connection.execute(
        """
        SELECT id
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if user is None:
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    updates = []
    values = []

    if data.username is not None and data.username != "string":
        updates.append("username = ?")
        values.append(data.username)

    if data.password is not None and data.password != "string":

        salt = secrets.token_bytes(16)

        password_hash = hash_password(
            data.password,
            salt
        )

        updates.append("password_hash = ?")
        values.append(password_hash)

    if data.role is not None and data.role != "string":
        updates.append("role = ?")
        values.append(data.role)

    if not updates:
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="No data provided for update"
        )

    values.append(user_id)

    connection.execute(
        f"""
        UPDATE users
        SET {", ".join(updates)}
        WHERE id = ?
        """,
        values
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "User updated successfully",
        "id": user_id
    }

# =========================
# DELETE USER
# =========================

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin_username: str,
    admin_password: str
):

    connection = get_connection()

    admin = connection.execute(
        """
        SELECT id, password_hash, role
        FROM user
        WHERE username = ?
        """,
        (admin_username,)
    ).fetchone

    if admin is None:
        connection.close

        raise HTTPException(
            status_code=403,
            detail="Invalid admin credentials"
        )

    if admin["role"] != "admin":
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    if not verify_password(
        admin_password,
        admin["password_hash"]
    ):
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Invalid admin credentials"
        )

    user = connection.execute(
        """
        SELECT id
        FROM user
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if user is None:
        connection.close

        raise HTTPException(
            status_code=400,
            detail="User not found"
        )

    if user_id == admin["id"]:
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Admin cannot delete themselves"
        )

    connection.execute(
        """
        DELETE FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "User successfully deleted",
        "id": user_id
    }

# =========================
# NUKE DATABASE
# =========================

@router.post("/users/nuke")
def reset_users_id():

    connection = get_connection()

    connection.execute("DELETE from users")

    connection.execute("DELETE FROM sqlite_sequence WHERE name='users'")

    connection.commit()
    connection.close()

    return {
        "message": "All users and IDs deleted"
    }