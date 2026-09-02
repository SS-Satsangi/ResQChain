from fastapi import APIRouter
from app.database import get_connection
from app.models.report import ReportCreate, ReportUpdate
from datetime import datetime

router = APIRouter()


@router.get("/incidents")
def get_incidents():
    connection = get_connection()

    incidents = connection.execute(
        "SELECT * FROM disasters"
    ).fetchall()

    connection.close()

    return {
        "incidents": [dict(incident) for incident in incidents]
    }


@router.post("/incidents")
def create_incident(report: ReportCreate):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO disasters (name, location, reported_at, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            report.name,
            report.location,
            datetime.now().isoformat(),
            report.status
        )
    )

    connection.commit()

    incident_id = cursor.lastrowid

    connection.close()

    return {
        "message": "Incident created successfully",
        "id": incident_id
    }

@router.patch("/incidents/{incident_id}")
def update_incident(incident_id: int, report: ReportUpdate):
    connection = get_connection()

    updates = []
    values = []

    if report.name is not None:
        updates.append("name = ?")
        values.append(report.name)

    if report.location is not None:
        updates.append("location = ?")
        values.append(report.location)

    if report.status is not None:
        updates.append("status = ?")
        values.append(report.status)

    if not updates:
        connection.close()
        return {
            "message": "No data provided for update"
        }

    values.append(incident_id)

    cursor = connection.execute(f"""
        UPDATE disasters
        SET {", ".join(updates)}
        WHERE id = ?
        """,
        values
    )

    connection.commit()

    connection.close()

    if cursor.rowcount == 0:
        return {
            "message": "Incident not found"
        }

    return {
        "message": "Incident updated successfully",
        "id": incident_id
    }

@router.delete("/incidents/{incident_id}")
def delete_incident(incident_id: int):
    connection = get_connection()

    cursor = connection.execute(
        "DELETE FROM disasters WHERE id = ?",
        (incident_id,)
    )

    connection.commit()

    connection.close()

    if cursor.rowcount == 0:
        return {
            "message": "Incident not found"
        }

    return {
        "message": "Incident deleted success",
        "id": incident_id
    }

@router.post("/incidents/nuke")
def reset_incidents_and_Id():
    connection = get_connection()

    connection.execute("DELETE FROM disasters")
    connection.execute(
        "DELETE FROM sqlite_sequence WHERE name = 'disasters'"
    )

    connection.commit()
    connection.close()

    return {
        "message": "All incidents deleted and ID counter reset"
    }