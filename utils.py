"""
Helper functions for security and the Brevo email dispatch API.
"""
import secrets
import hashlib
import json
import urllib.request
import urllib.error
from typing import Optional
from config import EMAIL_API_KEY, SENDER_EMAIL

def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{hashed.hex()}"

def verify_password(password: str, hashed_str: str) -> bool:
    try:
        salt, stored_hash = hashed_str.split(":")
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return secrets.compare_digest(computed.hex(), stored_hash)
    except Exception:
        return False

def send_real_verification_email(recipient_email: str, otp_code: str, verify_link: str):
    if not EMAIL_API_KEY or "YOUR_BREVO" in EMAIL_API_KEY:
        raise RuntimeError("Brevo API key is not configured.")
    
    payload = {
        "sender": {"name": "CampusAI Portal", "email": SENDER_EMAIL},
        "to": [{"email": recipient_email}],
        "subject": "Registration Verification",
        "htmlContent": f"<h3>Your code is: {otp_code}</h3><p>Or click: <a href='{verify_link}'>Verify</a></p>"
    }
    
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(payload).encode("utf-8"), headers={"api-key": EMAIL_API_KEY, "Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=8)

def send_password_reset_email(recipient_email: str, new_pass: str):
    if not EMAIL_API_KEY or "YOUR_BREVO" in EMAIL_API_KEY:
        raise RuntimeError("Brevo API key is not configured.")
        
    payload = {
        "sender": {"name": "CampusAI Portal", "email": SENDER_EMAIL},
        "to": [{"email": recipient_email}],
        "subject": "Temporary Password",
        "htmlContent": f"<h3>Your new password is: {new_pass}</h3>"
    }
    
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(payload).encode("utf-8"), headers={"api-key": EMAIL_API_KEY, "Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=8)
