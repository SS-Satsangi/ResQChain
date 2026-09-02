from fastapi import FastAPI
from app.routes import health, incidents
from app.database import initialize_database

app = FastAPI(
    title = "ResQChain API",
    version = "1.0.0"
)

initialize_database()

app.include_router(health.router)
app.include_router(incidents.router)