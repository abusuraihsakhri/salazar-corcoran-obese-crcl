"""
FastAPI REST API Server for Salazar Corcoran Obese Crcl.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor
from salazar_corcoran import calculate_metrics

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Salazar Corcoran Obese Crcl API",
    description="Reference CrCl calculation plus unvalidated prototype audit endpoints",
    version="3.0.0-ENTERPRISE",
)


class CrClRequest(BaseModel):
    sex: str
    age_years: float
    weight_kg: float
    height_m: float
    serum_creatinine_mg_dl: float


@app.post("/api/crcl")
def api_crcl(payload: CrClRequest):
    """Explicit clinical calculation, independent of the legacy mock audit system."""
    try:
        return calculate_metrics(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "salazar-corcoran-obese-crcl", "domain": "Clinical & Biomedical AI", "standard": "Prototype utility; no clinical certification", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_blocks_total": len(AuditLogger.get_trail()), "verified": AuditLogger.verify_integrity()}
