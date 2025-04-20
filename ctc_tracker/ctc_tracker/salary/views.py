import csv
from django.shortcuts import render, redirect
from .models import Salary, Employee  # Add Employee import here
from .forms import EmployeeLoginForm
from django.contrib import messages
from io import TextIOWrapper
from django.contrib.auth import logout
from datetime import datetime
import google.generativeai as genai
from django.conf import settings

def home(request):
    # Simulate getting salary data (you can replace this with dynamic DB fetching later)
    salary_data = Salary.objects.all()  # Fetch all salary data from the database
    return render(request, 'salary/home.html', {'salary': salary_data})

def upload_csv(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a .csv file.")
            return redirect("upload_csv")

        data_set = TextIOWrapper(csv_file.file, encoding="utf-8")
        reader = csv.DictReader(data_set, delimiter='\t')
        first_row = next(reader)
        print("DEBUG HEADERS:", first_row.keys())


        for raw_row in reader:
            row = {key.strip(): value.strip() for key, value in raw_row.items()}

            # Fetch employee object or create a new one
            employee, created = Employee.objects.get_or_create(employee_id=row["Employee ID"], employee_name=row["Employee Name"])

            Salary.objects.create(
                employee=employee,
                month=row["Month"],
                basic=row["Basic"],
                hra=row["HRA"],
                transport=row["Transport"],
                education=row["Education"],
                medical=row["Medical"],
                lta=row["LTA"],
                pf=row["PF"],
                pt=row["PT"],
            )

        messages.success(request, "Salary data uploaded successfully!")
        return redirect("home")

    return render(request, "salary/upload_csv.html")


# View to handle the login form for employees
def employee_login(request):
    if request.method == "POST":
        form = EmployeeLoginForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            try:
                employee = Employee.objects.get(employee_id=employee_id)
                request.session['employee_id'] = employee.employee_id  # ✅ Store in session
                return redirect('employee_dashboard')
            except Employee.DoesNotExist:
                messages.error(request, 'Invalid Employee ID')

    else:
        form = EmployeeLoginForm()

    return render(request, 'salary/employee_login.html', {'form': form})

MONTH_FORMAT = "%B %Y" 
def parse_month_str(month_str):
    try:
        return datetime.strptime(month_str, MONTH_FORMAT)
    except ValueError:
        return datetime.min  # fallback in case of bad data
    
# View to display the employee's dashboard after successful login
def employee_dashboard(request):
    employee_id = request.session.get('employee_id')
    if not employee_id:
        return redirect('employee_login')

    employee = Employee.objects.get(employee_id=employee_id)
    selected_month = request.GET.get('month')

    # Get all salary records and convert month strings to actual dates
    salary_records = Salary.objects.filter(employee=employee)
    available_months = salary_records.values_list('month', flat=True).distinct()
    
    # Convert to list of tuples: (original_str, parsed_date)
    month_tuples = [(m, parse_month_str(m)) for m in available_months]
    month_tuples.sort(key=lambda x: x[1], reverse=True)  # sort latest first

    sorted_months = [m[0] for m in month_tuples]

    if selected_month:
        salary = Salary.objects.filter(employee=employee, month=selected_month).first()
    else:
        latest_month = sorted_months[0] if sorted_months else None
        salary = Salary.objects.filter(employee=employee, month=latest_month).first()
        selected_month = latest_month

    return render(request, 'salary/employee_dashboard.html', {
        'employee': employee,
        'salary': salary,
        'available_months': sorted_months,
        'selected_month': selected_month,
    })

def employee_logout(request):
    logout(request)
    return redirect('employee_login')  # Redirect to login page after logout

from django.shortcuts import render, redirect
from .models import Employee, Salary

def salary_insights(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('employee_login')  # fallback if not logged in

    try:
        employee = Employee.objects.get(employee_id=emp_id)
        salary_data = Salary.objects.filter(employee=employee)

        insights = []
        for salary in salary_data:
            total_earnings = (
                salary.basic + salary.hra + salary.transport + 
                salary.education + salary.medical + salary.lta
            )
            total_deductions = salary.pf + salary.pt
            net_salary = total_earnings - total_deductions
            pf_percent = round((salary.pf / salary.basic) * 100, 2) if salary.basic else 0
            medical_percent = round((salary.medical / total_earnings) * 100, 2) if total_earnings else 0

            insights.append({
                "month": salary.month,
                "total_earnings": total_earnings,
                "total_deductions": total_deductions,
                "net_salary": net_salary,
                "pf_percent": pf_percent,
                "medical_percent": medical_percent,
            })

        context = {
            "employee": employee,
            "insights": insights
        }
        return render(request, 'salary/insights.html', context)

    except Employee.DoesNotExist:
        return redirect('employee_login')


genai.configure(api_key=settings.GOOGLE_API_KEY)


from django.shortcuts import render
from .models import Employee, Salary
import google.generativeai as genai

def salary_tips(request):
    # Retrieve the employee_id from the session
    emp_id = request.session.get('employee_id')
    
    if not emp_id:
        return render(request, 'salary/tips.html', {'tips': "Employee ID not found in session."})
    
    try:
        # Retrieve the employee object based on the employee_id from the session
        employee = Employee.objects.get(employee_id=emp_id)
        
        # Retrieve the most recent salary slip for the employee
        salary = Salary.objects.filter(employee=employee).order_by('-month').first()
        
        if salary:
            # Construct the prompt using the employee's name and salary details
            prompt = (
                f"Give useful and practical tips to help {employee.employee_name}, a software engineer in India, "
                f"make better use of their salary. They have the following salary details:\n\n"
                f"Basic: ₹{salary.basic}\n"
                f"HRA: ₹{salary.hra}\n"
                f"Transport: ₹{salary.transport}\n"
                f"Education: ₹{salary.education}\n"
                f"Medical: ₹{salary.medical}\n"
                f"LTA: ₹{salary.lta}\n\n"
                f"Provide short,simple,clear and concise suggestions based on these details. Provide bullet points"
            )
        else:
            prompt = f"Salary details not found for {employee.employee_name}. Please check the records."

        # Try generating content with the model
        model = genai.GenerativeModel("gemini-2.0-flash")  
        response = model.generate_content(prompt)
        tips = response.text

        # Split the response into paragraphs for better presentation
        formatted_tips = tips.split("\n")
        #formatted_tips = tips
        
    except Employee.DoesNotExist:
        formatted_tips = ["Employee not found in the database."]
    except Exception as e:
        formatted_tips = [f"Error generating tips: {e}"]

    return render(request, 'salary/tips.html', {'tips': formatted_tips})

def ask_ai(request):
    response_text = ""
    if request.method == "POST":
        user_prompt = request.POST.get("prompt")
        if user_prompt:
            try: 
                model = genai.GenerativeModel("gemini-2.0-flash")
                user_prompt += "Give short and concise answer in 10 lines"
                response = model.generate_content(user_prompt)
                response_text = response.text
            except Exception as e:
                response_text = f"Error generating response: {e}"

    return render(request, "salary/ask_ai.html", {"response": response_text})

def finance_news(request):
    prompt = """
    Give a brief summary (in simple terms) of the latest finance and economic news relevant to working professionals in India. 
    Limit to 4-5 bullet points. Avoid technical jargon.
    """

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        summary = response.text
    except Exception as e:
        summary = f"Error generating news summary: {e}"

    return render(request, "salary/news.html", {"summary": summary})

