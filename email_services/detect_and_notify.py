import pickle
import smtplib
from email.mime.text import MIMEText
from app import app
from models import User

# ==========================
# Load Model
# ==========================
model = pickle.load(open("spam_model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# ==========================
# Function to Send Alert Email
# ==========================
def send_notification(sender_email, sender_password, target_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = target_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Alert Email Sent to {target_email}!")
    except Exception as e:
        print("❌ Failed to send email:", e)

# ==========================
# Detect Spam Function
# ==========================
def detect_email(email_text):
    email_tfidf = vectorizer.transform([email_text])
    prediction = model.predict(email_tfidf)[0]

    with app.app_context():
        users = User.query.filter(User.app_email.isnot(None), User.app_password.isnot(None)).all()
        
        if prediction == 1:
            print("🚫 SPAM DETECTED!")
            for user in users:
                send_notification(
                    user.app_email,
                    user.app_password,
                    user.app_email,
                    "Spam Alert ⚠️",
                    f"The following message was detected as spam:\n\n{email_text[:150]}..."
                )
        else:
            print("✅ Not Spam.")

# ==========================
# Example Email (You Can Replace This)
# ==========================
if __name__ == "__main__":
    test_email = input("Enter email content to check across all accounts:\n")
    detect_email(test_email)