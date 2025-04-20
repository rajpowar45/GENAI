# models.py

from django.db import models

class Employee(models.Model):
    employee_id = models.CharField(max_length=50, unique=True)
    employee_name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.employee_name

class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.CharField(max_length=50)
    
    # Earnings
    basic = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2)
    transport = models.DecimalField(max_digits=10, decimal_places=2)
    education = models.DecimalField(max_digits=10, decimal_places=2)
    medical = models.DecimalField(max_digits=10, decimal_places=2)
    lta = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Deductions
    pf = models.DecimalField(max_digits=10, decimal_places=2)
    pt = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.employee.employee_name} - {self.month}"

    # Method to calculate the net salary (Earnings - Deductions)
    def net_salary(self):
        total_earnings = self.basic + self.hra + self.transport + self.education + self.medical + self.lta
        total_deductions = self.pf + self.pt
        return total_earnings - total_deductions


