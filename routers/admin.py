"""
Contains protected routes for master system control.
"""
import json
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas import AdminLoginRequest, CourseCreateRequest, StudentUpdateRequest
from database import load_database, save_database, DEFAULT_DATA
from config import ADMIN_STATIC_PASSWORD
from state import ACTIVE_ADMIN_SESSIONS, CHAT_HISTORY, OTP_STORE

router = APIRouter(prefix="/api/admin", tags=["Admin"])
security = HTTPBearer()

def require_admin(auth: HTTPAuthorizationCredentials = Security(security)):
    token = auth.credentials
    expiry = ACTIVE_ADMIN_SESSIONS.get(token)
    if not expiry or datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=401, detail="Session expired.")
    return True

@router.post("/login")
async def admin_login(req: AdminLoginRequest):
    if req.username == "admin" and secrets.compare_digest(req.password, ADMIN_STATIC_PASSWORD):
        token = secrets.token_hex(32)
        ACTIVE_ADMIN_SESSIONS[token] = datetime.now(timezone.utc) + timedelta(hours=2)
        return {"status": "success", "token": token}
    raise HTTPException(status_code=401, detail="Unauthorized.")

@router.get("/data")
async def admin_get_data(authorized: bool = Depends(require_admin)):
    db = load_database()
    sanitized = json.loads(json.dumps(db))
    for s in sanitized.get("students", {}).values():
        s.pop("password_hash", None)
    return sanitized

@router.post("/add-course")
async def admin_add_course(req: CourseCreateRequest, authorized: bool = Depends(require_admin)):
    db = load_database()
    code = req.code.upper().strip()
    db["courses"][code] = req.model_dump()
    save_database(db)
    return {"status": "success"}
