from flask import Flask,render_template,jsonify,request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import pickle
import json
import os
from models import db, User, EmailLog

app=Flask(__name__)
app.config['SECRET_KEY'] = 'spamsupersecretkey2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///email_spam_members.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

model=pickle.load(open("spam_model.pkl","rb"))
vectorizer=pickle.load(open("vectorizer.pkl","rb"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        app_email = request.form.get("app_email")
        app_password = request.form.get("app_password")
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password, app_email=app_email, app_password=app_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username")).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Login Unsuccessful.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def home():
    user_logs = EmailLog.query.filter_by(user_id=current_user.id).all()
    total = len(user_logs)
    spam = sum(1 for log in user_logs if log.prediction == 'Spam')
    ham = total - spam
    rate = round((spam / total) * 100, 1) if total > 0 else 0
    
    stats = {
        "total": total,
        "spam": spam,
        "ham": ham,
        "rate": rate
    }
    
    return render_template("index.html", stats=stats)

@app.route("/alerts_page")
@login_required
def alerts_page():
    return render_template("alerts.html")

@app.route("/history")
@login_required
def history():
    logs = EmailLog.query.filter_by(user_id=current_user.id).order_by(EmailLog.timestamp.desc()).all()
    # pass json module to parse the reasons back to list in jinja
    import json
    return render_template("history.html", logs=logs, json=json)
    
@app.route("/trends")
@login_required
def trends():
    user_logs = EmailLog.query.filter_by(user_id=current_user.id).all()
    total = len(user_logs)
    spam = sum(1 for log in user_logs if log.prediction == 'Spam')
    ham = total - spam
    
    stats = {
        "spam": spam,
        "ham": ham
    }
    return render_template("trends.html", stats=stats)

import imaplib
import email
from email.header import decode_header

@app.route("/inbox")
@login_required
def inbox():
    emails = []
    error = None
    try:
        EMAIL = current_user.app_email
        PASSWORD = current_user.app_password 
        
        if not EMAIL or not PASSWORD:
            return render_template("inbox.html", emails=[], error="Please register with an App Password to load your inbox.")
            
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")
        
        # Search for all emails, but fetch the last 10
        status, messages = mail.search(None, "ALL")
        if status == "OK" and messages[0]:
            email_ids = messages[0].split()
            latest_ids = email_ids[-10:] # get last 10
            
            for e_id in reversed(latest_ids):
                status, msg_data = mail.fetch(e_id, "(RFC822)")
                for part in msg_data:
                    if isinstance(part, tuple):
                        msg = email.message_from_bytes(part[1])
                        
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else 'utf-8')
                            
                        # Extract date
                        date_str = msg.get("Date", "")
                        
                        body = ""
                        if msg.is_multipart():
                            for p in msg.walk():
                                if p.get_content_type() == "text/plain":
                                    body_bytes = p.get_payload(decode=True)
                                    if body_bytes:
                                        body = body_bytes.decode('utf-8', errors='ignore')
                                    break
                        else:
                            body_bytes = msg.get_payload(decode=True)
                            if body_bytes:
                                body = body_bytes.decode('utf-8', errors='ignore')
                                
                        emails.append({
                            "subject": subject,
                            "date": date_str,
                            "body": body
                        })
        mail.logout()
    except Exception as e:
        error = f"Authentication to the email server failed. Make sure your app password is provided correctly: {e}"
        
    return render_template("inbox.html", emails=emails, error=error)

import re

priority_patterns = [
    r'\b(?:urgent|asap|immediately|deadline|action required|attention needed)\b',
    r'\b(?:payment overdue|invoice attached|account suspended|verify your identity)\b',
    r'\b(?:job offer|final interview|offer letter|onboarding)\b',
    r'\b(?:flight details|booking confirmation|itinerary)\b'
]

def extract_reasons(text, pred_prob, is_spam):
    reasons = []
    text_lower = text.lower()
    
    if is_spam and pred_prob > 0.85:
        reasons.append(f"High spam probability ({round(pred_prob * 100)}%)")
        
    promo_words = ['free', 'offer', 'guarantee', 'winner', 'cash', 'prize', 'urgent', 'buy', 'discount', 'cheap', 'click', 'subscribe']
    found_promo = [w for w in promo_words if w in text_lower]
    if found_promo:
        reasons.append(f"Contains promotional words: {', '.join(found_promo[:3])}")
        
    if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text):
        reasons.append("Suspicious links detected")
        
    if '$' in text or '£' in text or '€' in text:
        reasons.append("Mentions currency symbols often found in financial scams")
        
    if not reasons and is_spam:
        reasons.append("Message structure matches known spam patterns")
    elif not reasons and not is_spam:
        reasons.append("Appears to be normal conversation")
        
    return reasons

@app.route("/predict",methods=["POST"])
@login_required
def predict():
    text = request.form["email"]

    vec = vectorizer.transform([text])
    pred = model.predict(vec)[0]
    
    # Get probability of the predicted class (Class 1 is Spam)
    probabilities = model.predict_proba(vec)[0]
    spam_prob = probabilities[1]
    
    is_spam = bool(pred == 1)
    result = "Spam" if is_spam else "Ham"
    score = round(spam_prob * 100, 1)
    
    is_priority = False
    if not is_spam:
        text_lower = text.lower()
        for pattern in priority_patterns:
            if re.search(pattern, text_lower):
                is_priority = True
                break
                
    reasons = extract_reasons(text, spam_prob, is_spam)
    if is_priority:
        reasons.append("Identified as priority based on urgent keywords.")

    
    # Save to history
    log = EmailLog(
        body=text,
        prediction=result,
        probability=score,
        reasons=json.dumps(reasons),
        user_id=current_user.id
    )
    db.session.add(log)
    db.session.commit()
    
    # Re-calculate stats for the dashboard
    user_logs = EmailLog.query.filter_by(user_id=current_user.id).all()
    total = len(user_logs)
    spam = sum(1 for log in user_logs if log.prediction == 'Spam')
    ham = total - spam
    rate = round((spam / total) * 100, 1) if total > 0 else 0
    
    stats = {
        "total": total,
        "spam": spam,
        "ham": ham,
        "rate": rate
    }

    return render_template("index.html", 
                           prediction=True, 
                           is_spam=is_spam,
                           is_priority=is_priority,
                           score=score, 
                           reasons=reasons, 
                           email_text=text,
                           stats=stats)

@app.route("/alerts")
@login_required
def alerts():

    if os.path.exists("alerts.json"):
        all_alerts=json.load(open("alerts.json"))
        # Filter alerts that belong to the current user's connected app_email
        all_user_alerts = [a for a in all_alerts if a.get("user_email") == current_user.app_email]
        total_count = len(all_user_alerts)
        alerts = all_user_alerts[-10:]
    else:
        alerts=[]
        total_count = 0

    return jsonify({"alerts":alerts, "total_count": total_count})

@app.route("/priority")
@login_required
def priority():

    if os.path.exists("priority.json"):
        alerts=json.load(open("priority.json"))
    else:
        alerts=[]

    return jsonify({"alerts":alerts})

if __name__=="__main__":
    app.run(debug=True,port=5001)