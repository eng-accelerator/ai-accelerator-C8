from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, conint
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent


class StudentRequest(BaseModel):
    """Request schema for student data."""
    name: str = Field(
        ..., title="Student name", min_length=1, max_length=100, strip_whitespace=True
    )
    marks: conint(strict=True, ge=0, le=100) = Field(
        ..., title="Student marks"
    )


class StudentResponse(BaseModel):
    """Response schema for student results."""
    name: str
    marks: int
    grade: str


def calculate_grade(marks: int) -> str:
    """Compute the grade from marks following the defined grading scale."""
    if 90 <= marks <= 100:
        return "A"
    if 75 <= marks <= 89:
        return "B"
    if 60 <= marks <= 74:
        return "C"
    return "F"


app = FastAPI(
    title="Student Grading API",
    description="A simple FastAPI app to compute student grades from marks.",
    version="1.0.0",
)

# Enable CORS so the frontend can call the API when opened from a local file origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if True else ["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/students", response_model=StudentResponse)
def create_student_result(student: StudentRequest) -> StudentResponse:
    """Create a grade result for a given student payload."""
    grade = calculate_grade(student.marks)

    return StudentResponse(name=student.name, marks=student.marks, grade=grade)


@app.get("/", response_class=FileResponse)
def index() -> FileResponse:
    """Serve the static HTML frontend when the root URL is requested."""
    return FileResponse(BASE_DIR / "index.html")


# Notes:
# - Run the app with: python -m uvicorn app:app --reload
# - Open the frontend at: http://127.0.0.1:8000/
# - No database is used; this endpoint only computes a grade for each request.
