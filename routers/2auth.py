"""
Sets up the AI engine, tool bindings, and course query logic.
"""
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.tools import StructuredTool
from config import GROQ_API_KEY
from database import load_database, save_database

try:
    llm_primary = ChatGroq(model="openai/gpt-oss-120b", groq_api_key=GROQ_API_KEY, temperature=0, max_tokens=600)
    llm_backup_1 = ChatGroq(model="qwen/qwen3.8-27b", groq_api_key=GROQ_API_KEY, temperature=0, max_tokens=600)
    llm = llm_primary.with_fallbacks([llm_backup_1])
except Exception as e:
    llm = None
    llm_primary = None

def format_schedule_string(info):
    days = info.get("days", "")
    start = info.get("start_time", "").strip()
    end = info.get("end_time", "").strip()
    time_str = f"{start} to {end}" if start and end else (f"{start} onwards" if start else "TBA")
    return f"{days} | {time_str}" if days else time_str

def get_course_catalog_fn(course_code: Optional[str] = None, department: Optional[str] = None) -> str:
    db = load_database()
    results = []
    courses = db.get("courses", {})
    if course_code:
        code_clean = course_code.upper().strip()
        if code_clean in courses:
            info = courses[code_clean]
            status = "OPEN" if info.get("seats", 0) > 0 else "FULL"
            return f"• {code_clean}: {info.get('title')} | Seats: {info.get('seats')} ({status})"
        return f"Course not found."
    for code, info in courses.items():
        if department and info.get("dept", "").upper() != department.upper().strip():
            continue
        results.append(f"• {code}: {info.get('title')} | Seats: {info.get('seats')}")
    return "\n".join(results) if results else "No courses found."

def register_for_course_fn(student_id: str, course_code: str) -> str:
    db = load_database()
    student = db.get("students", {}).get(student_id)
    course = db.get("courses", {}).get(course_code.upper().strip())
    if not student or not course: return "Failed."
    if course.get("seats", 0) <= 0: return "Full."
    course["seats"] -= 1
    student["enrolled_courses"].append(course_code.upper().strip())
    save_database(db)
    return "Enrolled."

tools = [
    StructuredTool.from_function(func=get_course_catalog_fn, name="get_course_catalog", description="Retrieve courses."),
    StructuredTool.from_function(func=register_for_course_fn, name="register_for_course", description="Enroll student.")
]
tools_by_name = {t.name: t for t in tools}
llm_with_tools = llm_primary.bind_tools(tools, tool_choice="auto") if llm_primary else None
