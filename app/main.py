from app.base import BaseAudit
from fastapi import FastAPI
from .services import *
from app.database import engine
from app.tasks import celery

app = FastAPI()

# # Initialize database tables
@app.on_event("startup")
def startup():
    BaseAudit.metadata.create_all(bind=engine)

@app.post("/trigger_report")
async def trigger_report():
    report_id = report_service.prepare_report()
    celery.send_task('tasks.generate_report', args=[report_id])
    return report_id

@app.get("/get_report/{report_id}")
async def get_report(report_id: str):
    return report_service.get_report(report_id)

