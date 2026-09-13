"""
Holds in-memory temporary data that resets when the server restarts.
"""
from typing import Dict, Any, List
from datetime import datetime

ACTIVE_ADMIN_SESSIONS: Dict[str, datetime] = {}
OTP_STORE: Dict[str, Dict[str, Any]] = {}
CHAT_HISTORY: Dict[str, List[Any]] = {}
