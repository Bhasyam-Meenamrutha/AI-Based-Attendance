import sqlite3
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ============================================================
# SETTINGS
# ============================================================

DATABASE = "attendance.db"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Employee Attendance API",
    description="Backend API for the Employee Attendance System",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# PYDANTIC MODELS
# ============================================================

class EmployeeCreate(BaseModel):

    employee_id: str
    employee_name: str
    shift_start: str
    email: str


class TestAttendanceCreate(BaseModel):

    employee_id: str

    date: str

    check_in: str

    check_out: str | None = None


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Employee Attendance API is running"
    }


# ============================================================
# GET ALL EMPLOYEES
# ============================================================

@app.get("/employees")
def get_employees():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            employee_id,
            employee_name,
            shift_start,
            email
        FROM employees
        ORDER BY employee_id
    """)

    employees = cursor.fetchall()

    connection.close()

    return [
        dict(employee)
        for employee in employees
    ]


# ============================================================
# ADD EMPLOYEE
# ============================================================

@app.post("/employees")
def create_employee(
    employee: EmployeeCreate
):

    # --------------------------------------------------------
    # Validate shift format
    # --------------------------------------------------------

    try:

        datetime.strptime(
            employee.shift_start,
            "%H:%M"
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="shift_start must use HH:MM format, e.g. 14:00"
        )


    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Check whether employee already exists
    # --------------------------------------------------------

    cursor.execute("""
        SELECT employee_id
        FROM employees
        WHERE employee_id = ?
    """, (
        employee.employee_id,
    ))

    existing_employee = cursor.fetchone()


    if existing_employee:

        connection.close()

        raise HTTPException(
            status_code=409,
            detail="Employee already exists"
        )


    # --------------------------------------------------------
    # Insert employee
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO employees
        (
            employee_id,
            employee_name,
            shift_start,
            email
        )
        VALUES (?, ?, ?, ?)
    """, (
        employee.employee_id,
        employee.employee_name,
        employee.shift_start,
        employee.email
    ))


    connection.commit()

    connection.close()


    return {
        "message": "Employee created successfully",
        "employee": {
            "employee_id": employee.employee_id,
            "employee_name": employee.employee_name,
            "shift_start": employee.shift_start,
            "email": employee.email
        }
    }


# ============================================================
# GET ALL ATTENDANCE
# ============================================================

@app.get("/attendance")
def get_attendance():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            attendance.id,
            attendance.employee_id,
            employees.employee_name,
            employees.shift_start,
            attendance.date,
            attendance.check_in,
            attendance.check_out,
            attendance.late_minutes,
            attendance.late_email_sent

        FROM attendance

        LEFT JOIN employees
        ON attendance.employee_id = employees.employee_id

        ORDER BY
            attendance.date DESC,
            attendance.check_in DESC
    """)


    records = cursor.fetchall()

    connection.close()


    return [
        dict(record)
        for record in records
    ]


# ============================================================
# GET TODAY'S ATTENDANCE
# ============================================================

@app.get("/attendance/today")
def get_today_attendance():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            attendance.id,
            attendance.employee_id,
            employees.employee_name,
            employees.shift_start,
            attendance.date,
            attendance.check_in,
            attendance.check_out,
            attendance.late_minutes,
            attendance.late_email_sent

        FROM attendance

        LEFT JOIN employees
        ON attendance.employee_id = employees.employee_id

        WHERE attendance.date = DATE('now', 'localtime')

        ORDER BY attendance.check_in
    """)


    records = cursor.fetchall()

    connection.close()


    return [
        dict(record)
        for record in records
    ]


# ============================================================
# GET ATTENDANCE FOR ONE EMPLOYEE
# ============================================================

@app.get("/attendance/{employee_id}")
def get_employee_attendance(
    employee_id: str
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            attendance.id,
            attendance.employee_id,
            employees.employee_name,
            employees.shift_start,
            attendance.date,
            attendance.check_in,
            attendance.check_out,
            attendance.late_minutes,
            attendance.late_email_sent

        FROM attendance

        LEFT JOIN employees
        ON attendance.employee_id = employees.employee_id

        WHERE attendance.employee_id = ?

        ORDER BY attendance.date DESC
    """, (
        employee_id,
    ))


    records = cursor.fetchall()

    connection.close()


    return [
        dict(record)
        for record in records
    ]


# ============================================================
# TEST ATTENDANCE ENDPOINT
# ============================================================
#
# DEVELOPMENT ONLY
#
# This endpoint is NOT used by InsightFace.
#
# It allows us to test the backend from Swagger.
#
# ============================================================

@app.post("/attendance/test")
def create_test_attendance(
    attendance: TestAttendanceCreate
):

    # --------------------------------------------------------
    # Validate date
    # --------------------------------------------------------

    try:

        datetime.strptime(
            attendance.date,
            "%Y-%m-%d"
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="date must use YYYY-MM-DD format"
        )


    # --------------------------------------------------------
    # Validate check-in
    # --------------------------------------------------------

    try:

        datetime.strptime(
            attendance.check_in,
            "%H:%M"
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="check_in must use HH:MM format"
        )


    # --------------------------------------------------------
    # Validate check-out if provided
    # --------------------------------------------------------

    if attendance.check_out is not None:

        try:

            datetime.strptime(
                attendance.check_out,
                "%H:%M"
            )

        except ValueError:

            raise HTTPException(
                status_code=400,
                detail="check_out must use HH:MM format"
            )


    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Find employee
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            employee_id,
            employee_name,
            shift_start
        FROM employees
        WHERE employee_id = ?
    """, (
        attendance.employee_id,
    ))


    employee = cursor.fetchone()


    if employee is None:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )


    employee_id = employee["employee_id"]
    employee_name = employee["employee_name"]
    shift_start = employee["shift_start"]


    # --------------------------------------------------------
    # Check duplicate attendance
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id
        FROM attendance
        WHERE employee_id = ?
        AND date = ?
    """, (
        attendance.employee_id,
        attendance.date
    ))


    existing_record = cursor.fetchone()


    if existing_record:

        connection.close()

        raise HTTPException(
            status_code=409,
            detail="Attendance already exists for this employee and date"
        )


    # --------------------------------------------------------
    # Calculate late minutes
    # --------------------------------------------------------

    check_in_time = datetime.strptime(
        attendance.check_in,
        "%H:%M"
    )

    shift_time = datetime.strptime(
        shift_start,
        "%H:%M"
    )


    difference = (
        check_in_time - shift_time
    )


    late_minutes = int(
        difference.total_seconds() / 60
    )


    if late_minutes < 0:

        late_minutes = 0


    # --------------------------------------------------------
    # Email is NOT sent from this test endpoint
    # --------------------------------------------------------
    #
    # This is intentional.
    #
    # /attendance/test only tests the API/database.
    #
    # Real email sending happens through the
    # camera → attendance.py workflow.
    #
    # --------------------------------------------------------

    late_email_sent = 0


    # --------------------------------------------------------
    # Insert test attendance
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO attendance
        (
            employee_id,
            date,
            check_in,
            check_out,
            late_minutes,
            late_email_sent
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        attendance.employee_id,
        attendance.date,
        attendance.check_in,
        attendance.check_out,
        late_minutes,
        late_email_sent
    ))


    attendance_id = cursor.lastrowid


    connection.commit()

    connection.close()


    return {
        "message": "Test attendance created successfully",

        "attendance": {
            "id": attendance_id,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "shift_start": shift_start,
            "date": attendance.date,
            "check_in": attendance.check_in,
            "check_out": attendance.check_out,
            "late_minutes": late_minutes,
            "late_email_sent": False
        }
    }