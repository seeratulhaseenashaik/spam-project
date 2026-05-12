import imaplib
import email
from email.header import decode_header
import pickle
import json
import os
import re

from app import app
from models import User

model = pickle.load(open("spam_model.pkl","rb"))
vectorizer = pickle.load(open("vectorizer.pkl","rb"))

# More granular urgency definition
priority_patterns = [
    r'\b(?:urgent|asap|immediately|deadline|action required|attention needed)\b',
    r'\b(?:payment overdue|invoice attached|account suspended|verify your identity)\b',
    r'\b(?:job offer|final interview|offer letter|onboarding)\b',
    r'\b(?:flight details|booking confirmation|itinerary)\b'
]

def save_alert(file,data):
    if os.path.exists(file):
        alerts=json.load(open(file))
    else:
        alerts=[]
    alerts.append(data)
    json.dump(alerts,open(file,"w"),indent=2)

def monitor_all_users():
    with app.app_context():
        users = User.query.filter(User.app_email.isnot(None), User.app_password.isnot(None)).all()
        
        for user in users:
            EMAIL = user.app_email
            PASSWORD = user.app_password
            
            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(EMAIL,PASSWORD)
                mail.select("inbox")

                status,messages=mail.search(None,"UNSEEN")
                if not messages[0]:
                    mail.logout()
                    continue

                for num in messages[0].split():
                    status,msg_data=mail.fetch(num,"(RFC822)")

                    for part in msg_data:
                        if isinstance(part,tuple):
                            msg=email.message_from_bytes(part[1])
                            subject,_=decode_header(msg["Subject"])[0]

                            if isinstance(subject,bytes):
                                subject=subject.decode()

                            body=""
                            if msg.is_multipart():
                                for p in msg.walk():
                                    if p.get_content_type()=="text/plain":
                                        body=p.get_payload(decode=True).decode()
                                        break
                            else:
                                body=msg.get_payload(decode=True).decode()

                            text=body.lower()
                            vector=vectorizer.transform([body])
                            pred=model.predict(vector)[0]
                            
                            alert_data = {
                                "user_email": EMAIL,
                                "subject": subject,
                                "body": body[:150]
                            }

                            if pred==1:
                                alert_data["type"] = "spam"
                                save_alert("alerts.json", alert_data)
                            else:
                                alert_data["type"] = "ham"
                                save_alert("alerts.json", alert_data)

                                # Improvised Urgency Algorithm Check
                                is_priority = False
                                for pattern in priority_patterns:
                                    if re.search(pattern, text):
                                        is_priority = True
                                        break

                                if is_priority:
                                    priority_data = alert_data.copy()
                                    priority_data["link"] = "https://mail.google.com/"
                                    save_alert("priority.json", priority_data)

                mail.logout()
            except Exception as e:
                print(f"Skipping {EMAIL} due to error: {e}")

if __name__ == "__main__":
    monitor_all_users()