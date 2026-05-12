import smtplib
from email.mime.text import MIMEText
EMAIL = "seeratulhaseena@gmail.com"   # <-- your real email
PASSWORD = "pymagyxfdymfetis"       # app password (correct)  # no spaces

def send_notification(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_email

    # Connect using TLS
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()  # VERY IMPORTANT
    server.login(EMAIL, PASSWORD)

    server.send_message(msg)
    server.quit()

    print("✅ Email sent successfully!")

# Test
send_notification(
    "seeratulhaseena@gmail.com",
    "Spam Alert",
    "A spam email was detected."
)