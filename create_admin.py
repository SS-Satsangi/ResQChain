import hashlib
import secrets

from app.database import get_connection


def hash_password(password: str, salt: bytes) -> str:
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100_000
    )

    return f"{salt.hex()}:{password_hash.hex()}"


username = input("Enter admin username: ")
password = input("Enter admin password: ")

connection = get_connection()

existing_admin = connection.execute(
    """
    SELECT id
    FROM users
    WHERE username = ?
    """,
    (username,)
).fetchone()

if existing_admin:
    print("Username already exists.")
    connection.close()
    exit()

salt = secrets.token_bytes(16)

password_hash = hash_password(
    password,
    salt
)

connection.execute(
    """
    INSERT INTO users (
        username,
        password_hash,
        role
    )
    VALUES (?, ?, ?)
    """,
    (
        username,
        password_hash,
        "admin"
    )
)

connection.commit()
connection.close()

print("Admin account created successfully.") At the rate one two three unauthorized unauthorized around glad so no cala nindok sounded lag code