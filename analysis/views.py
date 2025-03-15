import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib import messages
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage

def admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:  # Only allow superusers (admins)
            login(request, user)
            return redirect("home")  # Redirect to home page after login
        else:
            return render(request, "admin_login.html", {"error": "Invalid Credentials"})

    return render(request, "admin_login.html")

def staff_login(request):
    if request.method == "POST":
        username = request.POST.get('username') 
        password = request.POST.get('password')
        user = authenticate(request, username, password=password)

        if user is not None and user.is_staff:  # Only allow staff members
            login(request, user)
            return redirect("home")  # Redirect to home page after login
        else:
            return render(request, "staff_login.html", {"error": "Invalid Credentials"})

    return render(request, "staff_login.html")

#Required columns for analysis
REQUIRED_COLUMNS = {"Student ID", "Name", "Total Marks", "Percentage", "Grade", "Subject1", "Subject2", "Subject3", "Subject4"}

def home(request):
    analysis_results = None
    file_url = None

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads/'))  
        filename = fs.save(excel_file.name, excel_file)
        file_url = fs.url(f'uploads/{filename}')
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)

        try:
            df = pd.read_excel(file_path)

            # Check for required columns
            if not REQUIRED_COLUMNS.issubset(df.columns):
                messages.error(request, "Invalid file format! Required columns missing.")
                return redirect("home")

            df["Grade"] = df["Grade"].astype(str).str.upper()  

            # Calculate pass/fail count
            pass_count = len(df[df["Percentage"] >= 40])
            fail_count = len(df[df["Percentage"] < 40])
            total_students = len(df)

            # Top 10 Students
            top_students = df.nlargest(10, "Total Marks")[["Name", "Total Marks"]]

            # Subject-wise Pass/Fail Ratio
            subject_pass_fail = {}
            for subject in ["Subject1", "Subject2", "Subject3", "Subject4"]:
                passed = len(df[df[subject] >= 40])
                failed = len(df[df[subject] < 40])
                subject_pass_fail[subject] = {"Pass": passed, "Fail": failed}

            # Grade Distribution
            grade_distribution = df["Grade"].value_counts()

            # Visualization Directory
            analysis_path = os.path.join(settings.MEDIA_ROOT, 'analysis')
            os.makedirs(analysis_path, exist_ok=True)

            ###  1. Pass/Fail Ratio - Pie Chart ###
            plt.figure(figsize=(5, 5))
            plt.pie([pass_count, fail_count], labels=["Passed", "Failed"], autopct='%1.1f%%', colors=["green", "red"], startangle=90)
            plt.title("Pass/Fail Ratio")
            plt.savefig(os.path.join(analysis_path, "pass_fail_pie.png"))
            plt.close()

            ###  2. Top 10 Students - Horizontal Bar Chart ###
            plt.figure(figsize=(6, 4))
            plt.barh(top_students["Name"], top_students["Total Marks"], color="blue")
            plt.xlabel("Total Marks")
            plt.title("Top 10 Students")
            plt.gca().invert_yaxis()
            plt.savefig(os.path.join(analysis_path, "top_students_bar.png"))
            plt.close()

            ###  3. Subject-wise Pass/Fail - Stacked Bar Chart ###
            subjects = list(subject_pass_fail.keys())
            pass_values = [subject_pass_fail[subject]["Pass"] for subject in subjects]
            fail_values = [subject_pass_fail[subject]["Fail"] for subject in subjects]

            plt.figure(figsize=(6, 4))
            plt.bar(subjects, pass_values, color="green", label="Pass")
            plt.bar(subjects, fail_values, color="red", bottom=pass_values, label="Fail")
            plt.title("Subject-wise Pass/Fail Ratio")
            plt.legend()
            plt.savefig(os.path.join(analysis_path, "subject_pass_fail_bar.png"))
            plt.close()

            ###  4. Grade Distribution - Donut Chart ###
            plt.figure(figsize=(6, 6))
            wedges, texts, autotexts = plt.pie(grade_distribution, labels=grade_distribution.index, autopct='%1.1f%%', colors=["purple", "blue", "orange", "green", "red"])
            centre_circle = plt.Circle((0,0),0.70,fc='white')  # Create donut effect
            fig = plt.gcf()
            fig.gca().add_artist(centre_circle)
            plt.title("Grade Distribution")
            plt.savefig(os.path.join(analysis_path, "grade_distribution_donut.png"))
            plt.close()

            ###  5. Subject-wise Performance - Line Chart ###
            subject_means = df[["Subject1", "Subject2", "Subject3", "Subject4"]].mean()
            plt.figure(figsize=(6, 4))
            plt.plot(subject_means.index, subject_means.values, marker='o', linestyle='-', color="orange")
            plt.title("Average Performance Across Subjects")
            plt.xlabel("Subjects")
            plt.ylabel("Average Marks")
            plt.grid()
            plt.savefig(os.path.join(analysis_path, "subject_performance_line.png"))
            plt.close()

            analysis_results = {
                "total_students": total_students,
                "pass_count": pass_count,
                "fail_count": fail_count,
            }
            messages.success(request, "File uploaded and analysis generated successfully!")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect("home")

    return render(request, 'index.html', {"file_url": file_url, "analysis_results": analysis_results})

def user_logout(request):
    logout(request)
    return redirect("admin_login") 