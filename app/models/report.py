from pydantic import BaseModel

class ReportCreate(BaseModel):
    name: str
    location: str
    status: str

class ReportUpdata(BaseModel):
    name: str | None = None
    location: str | None = None
    status: str | None = None