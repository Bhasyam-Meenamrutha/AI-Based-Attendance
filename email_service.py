import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# ============================================================
# SEND EMAIL
# ============================================================

def send_late_email(
    employee_name,
    employee_email,
    check_in,
    shift_start,
    late_minutes
):

    # --------------------------------------------------------
    # Check email configuration
    # --------------------------------------------------------

    if not EMAIL_SENDER or not EMAIL_PASSWORD:

        print("Email configuration is missing.")

        return False


    # --------------------------------------------------------
    # Create email
    # --------------------------------------------------------

    message = EmailMessage()

    message["From"] = EMAIL_SENDER

    message["To"] = employee_email

    message["Subject"] = (
        "Late Arrival Notification"
    )


    # --------------------------------------------------------
    # Email body
    # --------------------------------------------------------

    message.set_content(
        f"""
Hello {employee_name},

This is an automated attendance notification.

Your attendance details for today:

Employee       : {employee_name}
Shift Start    : {shift_start}
Check-in Time  : {check_in}
Late By        : {late_minutes} minutes

Please ensure that you follow your assigned shift timings.

This is an automatically generated email.
Please do not reply to this email.

Regards,
Employee Attendance System
"""
    )


    # --------------------------------------------------------
    # Connect to Gmail SMTP server
    # --------------------------------------------------------

    try:

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as server:

            # Start secure connection

            server.starttls()


            # Login

            server.login(
                EMAIL_SENDER,
                EMAIL_PASSWORD
            )


            # Send email

            server.send_message(
                message
            )


        print(
            f"Late-arrival email sent to "
            f"{employee_email}"
        )

        return True


    except Exception as error:

        print(
            "Failed to send email:"
        )

        print(error)

        return False