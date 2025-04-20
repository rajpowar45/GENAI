from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("upload/", views.upload_csv, name="upload_csv"),
    path('employee-login/', views.employee_login, name='employee_login'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee-logout/', views.employee_logout, name='employee_logout'),
    path("insights/", views.salary_insights, name="salary_insights"),
    path('tips/', views.salary_tips, name='salary_tips'),
    path('ask/', views.ask_ai, name='ask_ai'),
    path("news/", views.finance_news, name="finance_news"),
 
]


