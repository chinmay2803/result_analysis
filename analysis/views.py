import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib import messages
from .models import StudentResult
import pymysql

def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",  # Change if needed
        password="",  # Your MySQL password
        database="result_analysis",
        cursorclass=pymysql.cursors.DictCursor
    )

def admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='admin'", (username, password))
                user = cursor.fetchone()
            
            conn.close()

            if user:
                request.session["user_id"] = user["id"]
                request.session["role"] = user["role"]
                request.session["username"] = user["username"]

                messages.success(request, "Login successful!")

                print("User logged in:", request.session.get("username"))  # Debugging

                return redirect("home")
            else:
                messages.error(request, "Invalid credentials")
                return redirect("admin_login")

        except Exception as e:
            messages.error(request, f"Database error: {str(e)}")

    return render(request, "admin_login.html")


def staff_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='staff'", (username, password))
                user = cursor.fetchone()
            
            conn.close()

            if user:
                request.session["user_id"] = user["id"]
                request.session["role"] = user["role"]
                messages.success(request, "Login successful!")
                return redirect("home")
            else:
                messages.error(request, "Invalid credentials")
                return redirect("staff_login")

        except Exception as e:
            messages.error(request, f"Database error: {str(e)}")
            return redirect("staff_login")

    return render(request, "staff_login.html")

REQUIRED_COLUMNS = {"Student ID", "Name", "Total Marks", "Percentage", "Grade", "Subject1", "Subject2", "Subject3", "Subject4"}

def home(request):
    if "user_id" not in request.session:  # Custom session check
        messages.error(request, "You must log in first!")
        return redirect("admin_login")

    analysis_results = None
    file_url = None

    print("Session user_id:", request.session.get("user_id"))  # Debugging

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads/'))  
        filename = fs.save(excel_file.name, excel_file)
        file_url = fs.url(f'uploads/{filename}')
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)

        try:
            df = pd.read_excel(file_path)
            if not REQUIRED_COLUMNS.issubset(df.columns):
                messages.error(request, "Invalid file format! Required columns missing.")
                return redirect("home")

            df["Grade"] = df["Grade"].astype(str).str.upper()
            for _, row in df.iterrows():
                StudentResult.objects.update_or_create(
                    student_id=row["Student ID"],
                    defaults={
                        "name": row["Name"],
                        "total_marks": row["Total Marks"],
                        "percentage": row["Percentage"],
                        "grade": row["Grade"],
                        "subject1": row["Subject1"],
                        "subject2": row["Subject2"],
                        "subject3": row["Subject3"],
                        "subject4": row["Subject4"],
                    },
                )
            messages.success(request, "File uploaded and data saved successfully!")
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect("home")

    return render(request, 'index.html', {"file_url": file_url, "analysis_results": analysis_results})


def user_logout(request):
    logout(request)
    request.session.flush()
    messages.success(request, "You have been logged out!")
    return redirect("admin_login")
