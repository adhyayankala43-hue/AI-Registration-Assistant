"""
Manages all authentication, OTP, and registration logic.
"""

import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from schemas import SendOTPRequest, VerifyOTPRequest, StudentRegisterRequest, StudentLoginRequest, ForgotPasswordRequest
from utils import send_real_verification_email, send_password_reset_email, hash_password, verify_password
from database import load_database, save_database
from state import OTP_STORE
from config import APP_BASE_URL

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/send-otp")
async def handle_send_otp(req: SendOTPRequest):
    email = req.target.lower().strip()
    otp_val = f"{secrets.randbelow(900000) + 100000}"
    link_token = secrets.token_urlsafe(32)
    verify_link = f"{APP_BASE_URL}/verify-email-link?email={email}&token={link_token}"
    OTP_STORE[email] = {"otp": otp_val, "token": link_token, "verified": False, "attempts": 0, "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)}
    send_real_verification_email(email, otp_val, verify_link)
    return {"status": "success", "message": "Email sent."}

@router.post("/verify-otp")
async def handle_verify_otp(req: VerifyOTPRequest):
    email = req.target.lower().strip()
    record = OTP_STORE.get(email)
    if not record or datetime.now(timezone.utc) > record["expires_at"]:
        raise HTTPException(status_code=400, detail="Code expired.")
    if not secrets.compare_digest(record["otp"], req.otp.strip()):
        raise HTTPException(status_code=400, detail="Invalid passcode.")
    record["verified"] = True
    return {"status": "success"}

@router.post("/register-student")
async def register_student(req: StudentRegisterRequest):
    email = req.email.lower().strip()
    if not OTP_STORE.get(email, {}).get("verified", False):
        raise HTTPException(status_code=403, detail="Verification required.")
    db = load_database()
    new_id = str(int(max(db["students"].keys(), key=lambda x: int(x) if x.isdigit() else 10000)) + 1) if db["students"] else "10001"
    db["students"][new_id] = {"name": req.name, "email": email, "phone": req.phone, "password_hash": hash_password(req.password), "field": req.course, "enrolled_courses": []}
    save_database(db)
    return {"status": "success", "student_id": new_id, "name": req.name}

@router.post("/student-login")
async def student_login(req: StudentLoginRequest):
    db = load_database()
    for sid, sdata in db["students"].items():
        if sdata.get("email") == req.email.lower().strip() and verify_password(req.password, sdata.get("password_hash", "")):
            return {"status": "success", "student_id": sid, "student": {"name": sdata["name"]}}
    raise HTTPException(status_code=401, detail="Invalid credentials.")
