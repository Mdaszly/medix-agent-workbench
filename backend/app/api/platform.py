from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from app.core.database import add_appointment, appointment_counts, cancel_appointment, list_appointments, list_encounters
from app.schemas.chat import ChatRequest
from app.services.medical_business import (
    ConsultationService,
    departments,
    interpret_report,
    report_list,
    schedule_for_department,
)

router = APIRouter(prefix="/api", tags=["platform"])
service = ConsultationService()


@router.post("/triage")
async def triage(req: ChatRequest):
    return await service.chat(req, scene="triage")


@router.post("/consultation")
async def consultation(req: ChatRequest):
    return await service.chat(req, scene="consultation")


@router.post("/medication")
async def medication(req: ChatRequest):
    return await service.chat(req, scene="medication")


@router.get("/records")
async def records(user_id: str = "demo_user", days: int = Query(default=7, ge=1, le=365)):
    return {"records": list_encounters(user_id=user_id, days=days)}


@router.get("/reports")
async def reports():
    return {"reports": report_list()}


@router.get("/reports/{report_id}/interpret")
async def report_interpretation(report_id: str):
    return await interpret_report(report_id)


@router.get("/departments")
async def department_list():
    return {"departments": departments()}


@router.get("/appointments/schedule")
async def appointment_schedule(department: str = "呼吸科", user_id: str = "demo_user"):
    return schedule_for_department(department, appointment_counts(user_id=user_id))


@router.post("/appointments")
async def create_appointment(payload: Dict[str, Any]):
    if int(payload.get("remaining", 1)) <= 0:
        raise HTTPException(status_code=400, detail="当前号源已约满")
    appointment_id = add_appointment(payload)
    return {"ok": True, "appointment_id": appointment_id, "appointments": list_appointments(payload.get("user_id", "demo_user"))}


@router.get("/appointments")
async def appointments(user_id: str = "demo_user"):
    return {"appointments": list_appointments(user_id=user_id)}


@router.delete("/appointments/{appointment_id}")
async def appointment_cancel(appointment_id: int, user_id: str = "demo_user"):
    ok = cancel_appointment(appointment_id, user_id=user_id)
    return {"ok": ok, "appointments": list_appointments(user_id=user_id)}
