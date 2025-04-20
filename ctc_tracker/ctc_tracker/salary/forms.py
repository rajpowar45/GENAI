# forms.py

from django import forms

class EmployeeLoginForm(forms.Form):
    employee_id = forms.CharField(max_length=50, label="Employee ID", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Employee ID'}))
