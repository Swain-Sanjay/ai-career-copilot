from flask import Flask, render_template, request, redirect, session
from db import Base, engine, SessionLocal
import models
import pdfplumber
import docx
import json
from ai import analyze_resume

app = Flask(
    __name__,
    template_folder="templates", 
    static_folder="static"
)
app.secret_key= "secret123"

import os

print("Current directory:", os.getcwd())
print("Templates exists:", os.path.exists("templates"))
print("Login exists:", os.path.exists("templates/login.html"))

Base.metadata.create_all(bind=engine)

#---HOME
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

#---SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = db.query(models.User).filter_by(email=email).first()
        if existing_user:
            return "User already exists"
        
        user = models.User(email=email, password=password)
        db.add(user)
        db.commit()

        return redirect("/login")
    
    return render_template("signup.html")

#--LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.query(models.User).filter_by(email=email, password= password).first()
 
        if user:
            session["user"] = user.email
            return redirect("/dashboard")
        else:
            return "Invalid credentials"
    return render_template("login.html")    

#--DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":

        print("FORM SUBMITTED")

        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")
        print("RESUME TEXT =, resume_text")

        file = request.files.get("file")

        print("REQUEST FILES =", request.files)
        print("FILENAME =", file.filename if file else "NO FILE")
        print("FILE =", file)

        if file and file.filename:

            if file.filename.lower().endswith(".pdf"):
                try:
                    with pdfplumber.open(file) as pdf:

                        print("TOTAL PAGES =", len(pdf.pages))

                        text = ""

                        for i, page in enumerate(pdf.pages):
                            page_text = page.extract_text()

                            print(f"PAGE {i+1} TEXT =", repr(page_text))

                            if page_text:
                                text += page_text + "\n"

                        resume_text = text

                        print("RESUME LENGTH =", len(resume_text))
                        print("FIRST 200 CHARS =", resume_text[:200])

                except Exception as e:
                    result = {"error": f"PDF error: {str(e)}"}

            elif file.filename.lower().endswith(".docx"):
                try:
                    doc = docx.Document(file)

                    text = ""

                    for para in doc.paragraphs:
                        text += para.text + "\n"

                    resume_text = text

                except Exception as e:
                    result = {"error": f"DOCX error: {str(e)}"}

            else:
                result = {
                    "error": "Unsupported file type. Please upload a PDF or DOCX."
                }

        if resume_text and user_goal and result is None:
            try:
                print("CALLING AI ANALYSIS")

                result = analyze_resume(
                    resume_text,
                    user_goal
                )

                print("RESULT =", result)

                db = SessionLocal()

                user = db.query(models.User).filter_by(
                    email=session["user"]
                ).first()

                if user:
                    report = models.Report(
                        user_id=user.id,
                        resume_text=resume_text,
                        result=json.dumps(result)
                    )

                    db.add(report)
                    db.commit()

            except Exception as e:
                result = {"error": f"AI error: {str(e)}"}

    username = session["user"].split("@")[0].title()
    return render_template(
        "dashboard.html",
        user=username,
        result=result
    )

#History
@app.route("/history")       
def history():
    if "user" not in session:
        return redirect("/login")
    
    db = SessionLocal()
    user = db.query(models.User).filter_by(email=session["user"]).first()

    reports = db.query(models.Report).filter_by(user_id = user.id).all()

    #convert JSON string > dict
    parsed_reports = []
    for r in reports:
        try:
            parsed_result = json.loads(r.result)
            print("PARSED RESULT =", parsed_result)
        except Exception as e:
            print("ERROR =", e)
            parsed_result = {}

        parsed_reports.append({
            "resume": r.resume_text,
            "result": parsed_result
        })

    return render_template("history.html", reports=parsed_reports)


#Logout route
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

if __name__ == "__main__":                   
    app.run(debug=True)