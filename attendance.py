import sqlite3
from datetime import datetime

from email_service import send_late_email


DATABASE = "attendance.db"

MINIMUM_WORK_MINUTES = 60


# ============================================================
# DATABASE
# ============================================================

def create_database():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Employees table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            employee_name TEXT NOT NULL,
            shift_start TEXT NOT NULL,
            email TEXT
        )
    """)

    # --------------------------------------------------------
    # Attendance table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            late_minutes INTEGER DEFAULT 0
        )
    """)

    connection.commit()


    # ========================================================
    # DATABASE MIGRATION
    # ========================================================

    # Check existing attendance columns

    cursor.execute("""
        PRAGMA table_info(attendance)
    """)

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]


    # Add late_email_sent if it doesn't exist

    if "late_email_sent" not in columns:

        cursor.execute("""
            ALTER TABLE attendance
            ADD COLUMN late_email_sent INTEGER DEFAULT 0
        """)


    # Check employee columns

    cursor.execute("""
        PRAGMA table_info(employees)
    """)

    employee_columns = [
        column[1]
        for column in cursor.fetchall()
    ]


    # Add email column if it doesn't exist

    if "email" not in employee_columns:

        cursor.execute("""
            ALTER TABLE employees
            ADD COLUMN email TEXT
        """)


    connection.commit()
    connection.close()


# ============================================================
# ADD EMPLOYEE
# ============================================================

def add_employee(
    employee_id,
    employee_name,
    shift_start,
    email
):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()


    cursor.execute("""
        INSERT OR REPLACE INTO employees
        (
            employee_id,
            employee_name,
            shift_start,
            email
        )
        VALUES (?, ?, ?, ?)
    """, (
        employee_id,
        employee_name,
        shift_start,
        email
    ))


    connection.commit()
    connection.close()


    print(
        f"Employee {employee_id} added successfully."
    )


# ============================================================
# GET EMPLOYEE
# ============================================================

def get_employee(employee_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            employee_id,
            employee_name,
            shift_start,
            email
        FROM employees
        WHERE employee_id = ?
    """, (
        employee_id,
    ))


    employee = cursor.fetchone()

    connection.close()

    return employee


# ============================================================
# CALCULATE LATE MINUTES
# ============================================================

def calculate_late_minutes(
    current_time,
    shift_start
):

    current = datetime.strptime(
        current_time,
        "%H:%M"
    )

    shift = datetime.strptime(
        shift_start,
        "%H:%M"
    )


    difference = current - shift


    late_minutes = int(
        difference.total_seconds() / 60
    )


    if late_minutes < 0:

        late_minutes = 0


    return late_minutes


# ============================================================
# CHECK EMPLOYEE ATTENDANCE
# ============================================================

def check_employee_attendance(employee_id):

    # --------------------------------------------------------
    # Find employee
    # --------------------------------------------------------

    employee = get_employee(
        employee_id
    )


    if employee is None:

        print(
            "Employee not found."
        )

        return


    (
        employee_id,
        employee_name,
        shift_start,
        employee_email
    ) = employee


    # --------------------------------------------------------
    # Current date and time
    # --------------------------------------------------------

    now = datetime.now()

    current_time = now.strftime(
        "%H:%M"
    )

    current_date = now.strftime(
        "%Y-%m-%d"
    )


    # --------------------------------------------------------
    # Connect database
    # --------------------------------------------------------

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Find today's attendance
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            check_in,
            check_out,
            late_minutes,
            late_email_sent
        FROM attendance
        WHERE employee_id = ?
        AND date = ?
    """, (
        employee_id,
        current_date
    ))


    record = cursor.fetchone()


    # ========================================================
    # CASE 1 — FIRST RECOGNITION TODAY
    # ========================================================

    if record is None:

        # Calculate late minutes

        late_minutes = calculate_late_minutes(
            current_time,
            shift_start
        )


        # ----------------------------------------------------
        # Insert attendance
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO attendance
            (
                employee_id,
                date,
                check_in,
                late_minutes,
                late_email_sent
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            employee_id,
            current_date,
            current_time,
            late_minutes,
            0
        ))


        attendance_id = cursor.lastrowid


        connection.commit()


        # ----------------------------------------------------
        # Print check-in information
        # ----------------------------------------------------

        print()
        print(
            "CHECK-IN RECORDED"
        )
        print(
            "------------------"
        )
        print(
            f"Employee : {employee_name}"
        )
        print(
            f"ID       : {employee_id}"
        )
        print(
            f"Shift    : {shift_start}"
        )
        print(
            f"Check-in : {current_time}"
        )
        print(
            f"Late     : {late_minutes} minutes"
        )


        # ====================================================
        # SEND LATE EMAIL
        # ====================================================

        if late_minutes > 0:

            if employee_email:

                print()
                print(
                    "Sending late-arrival email..."
                )


                email_sent = send_late_email(
                    employee_name=employee_name,
                    employee_email=employee_email,
                    check_in=current_time,
                    shift_start=shift_start,
                    late_minutes=late_minutes
                )


                if email_sent:

                    cursor.execute("""
                        UPDATE attendance
                        SET late_email_sent = 1
                        WHERE id = ?
                    """, (
                        attendance_id,
                    ))


                    connection.commit()


                    print(
                        "Late-arrival email recorded as sent."
                    )


                else:

                    print(
                        "Email could not be sent."
                    )

            else:

                print(
                    "Employee email is not configured."
                )


        connection.close()

        return


    # ========================================================
    # EXISTING ATTENDANCE RECORD
    # ========================================================

    (
        attendance_id,
        check_in,
        check_out,
        late_minutes,
        late_email_sent
    ) = record


    # ========================================================
    # CASE 2 — ALREADY CHECKED OUT
    # ========================================================

    if check_out is not None:

        print()
        print(
            "ATTENDANCE ALREADY COMPLETED"
        )
        print(
            "-----------------------------"
        )
        print(
            f"Employee  : {employee_name}"
        )
        print(
            f"Check-in  : {check_in}"
        )
        print(
            f"Check-out : {check_out}"
        )


        connection.close()

        return


    # ========================================================
    # CASE 3 — CHECKED IN BUT NOT CHECKED OUT
    # ========================================================

    check_in_datetime = datetime.strptime(
        check_in,
        "%H:%M"
    )

    current_datetime = datetime.strptime(
        current_time,
        "%H:%M"
    )


    worked_minutes = int(
        (
            current_datetime
            - check_in_datetime
        ).total_seconds() / 60
    )


    # --------------------------------------------------------
    # Prevent immediate check-out
    # --------------------------------------------------------

    if worked_minutes < MINIMUM_WORK_MINUTES:

        print()
        print(
            "CHECK-IN ALREADY RECORDED"
        )
        print(
            "-------------------------"
        )
        print(
            f"Employee       : {employee_name}"
        )
        print(
            f"Check-in       : {check_in}"
        )
        print(
            f"Current time   : {current_time}"
        )
        print(
            f"Minutes passed : {worked_minutes}"
        )
        print(
            "Status         : Still inside"
        )


        connection.close()

        return


    # ========================================================
    # CASE 4 — CHECK-OUT
    # ========================================================

    cursor.execute("""
        UPDATE attendance
        SET check_out = ?
        WHERE id = ?
    """, (
        current_time,
        attendance_id
    ))


    connection.commit()
    connection.close()


    print()
    print(
        "CHECK-OUT RECORDED"
    )
    print(
        "-------------------"
    )
    print(
        f"Employee : {employee_name}"
    )
    print(
        f"Check-in : {check_in}"
    )
    print(
        f"Check-out: {current_time}"
    )
    print(
        f"Worked   : {worked_minutes} minutes"
    )


# ============================================================
# TEST / SETUP
# ============================================================

if __name__ == "__main__":

    create_database()

    add_employee(
        employee_id="6495",
        employee_name="naveen chowdari",
        shift_start="14:00",
        email="nookanaveenth@gmail.com"
    )

    print()
    print(
        "Database and employee setup completed."
    )