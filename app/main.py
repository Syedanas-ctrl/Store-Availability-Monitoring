from app.base import BaseAudit
from app.config import Config
from fastapi import FastAPI
from .services import *
from app.database import engine
from app.tasks import celery
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [Config.ORIGIN]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    BaseAudit.metadata.create_all(bind=engine)

@app.post("/trigger_report")
async def trigger_report():
    report_id = report_service.prepare_report()
    celery.send_task('tasks.generate_report', args=[report_id])
    return str(report_id)

@app.get("/get_report/{report_id}")
async def get_report(report_id: str):
    return report_service.get_report(report_id)

