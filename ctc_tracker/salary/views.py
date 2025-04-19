import csv
from django.shortcuts import render, redirect
from .models import Salary, Employee  # Add Employee import here
from .forms import EmployeeLoginForm
from django.contrib import messages
from io import TextIOWrapper
from django.contrib.auth import logout

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

# View to display the employee's dashboard after successful login
def employee_dashboard(request):
    # Get the employee ID from session
    employee_id = request.session.get('employee_id')

    if not employee_id:
        return redirect('employee_login')  # Redirect to login if session doesn't exist

    employee = Employee.objects.get(employee_id=employee_id)
    salary_data = Salary.objects.filter(employee=employee)  # Fetch the salary data for the logged-in employee

    return render(request, 'salary/employee_dashboard.html', {'employee': employee, 'salary_data': salary_data})

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



