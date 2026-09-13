"""
Contains all Pydantic models to strictly validate incoming API requests.
"""
import re
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

TIME_PATTERN = r"^(1[0-2]|0?[1-9]):[0-5][0-9] (AM|PM)$"
DAYS_PATTERN = r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)(/(Mon|Tue|Wed|Thu|Fri|Sat|Sun))*$"

class AdminLoginRequest(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=100)

class StudentUpdateRequest(BaseModel):
    student_id: str
    name: str = Field(..., max_length=100, pattern=r"^[a-zA-Z\s]+$")
    email: str = Field(..., max_length=100)
    field: str = Field(..., max_length=100)

class CourseCreateRequest(BaseModel):
    code: str = Field(..., max_length=10, pattern=r"^[A-Za-z]{2,4}\d{2,4}$")
    title: str = Field(..., max_length=100, pattern=r"^[0-9\s\-\&,]*[a-zA-Z][a-zA-Z0-9\s\-\&,]*$")
    dept: str = Field(..., max_length=10, pattern=r"^[A-Za-z]+$")
    credits: int = Field(..., ge=1, le=10)
    seats: int = Field(..., ge=0)
    days: str = Field(..., max_length=50, pattern=DAYS_PATTERN)
    start_time: str = Field(..., pattern=TIME_PATTERN)
    end_time: str = Field(default="", max_length=20)

    @model_validator(mode='after')
    def validate_time_bounds(self) -> 'CourseCreateRequest':
        if self.end_time:
            if not re.match(TIME_PATTERN, self.end_time):
                raise ValueError("end_time must match 'HH:MM AM/PM' format")
            start_dt = datetime.strptime(self.start_time, "%I:%M %p")
            end_dt = datetime.strptime(self.end_time, "%I:%M %p")
            if start_dt >= end_dt:
                raise ValueError("Strict Time Bound Error: end_time must be strictly after start_time.")
        return self

class CourseUpdateRequest(CourseCreateRequest):
    code: str = Field(default="", exclude=True) # Reuses logic but removes code

class SendOTPRequest(BaseModel):
    target: str = Field(..., max_length=100)

class VerifyOTPRequest(BaseModel):
    target: str = Field(..., max_length=100)
    otp: str = Field(..., min_length=6, max_length=6)

class StudentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60, pattern=r"^[a-zA-Z\s]+$")
    email: str = Field(..., max_length=100)
    phone: str = Field(..., pattern=r"^\+91[6-9]\d{9}$")
    password: str = Field(..., min_length=8, max_length=64)
    course: str = Field(..., max_length=50)

    @model_validator(mode='after')
    def validate_phone_not_dummy(self) -> 'StudentRegisterRequest':
        local_num = self.phone[3:]
        if len(set(local_num)) == 1 or local_num in ["9876543210", "6789012345"]:
            raise ValueError("Dummy phone numbers are not allowed.")
        return self

class StudentLoginRequest(BaseModel):
    email: str = Field(..., max_length=100)
    password: str = Field(..., max_length=64)

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=100)

class ChatRequest(BaseModel):
    student_id: str
    message: str = Field(..., max_length=500)
