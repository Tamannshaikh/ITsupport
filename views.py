from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import CustomUser, IssueReport
from django.views.decorators.csrf import csrf_exempt
import uuid
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.utils import timezone




def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.role == 'manager':
                return redirect('manager_home')
            elif user.role == 'issue_reporter':
                return redirect('issue_reporter_home')
            elif user.role == 'support_engineer':
                return redirect('support_engineer_home')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')

from django.http import HttpResponse

# def manager_home(request):
#     return HttpResponse("Welcome Manager!")

def manager_home(request):
    if not request.user.is_authenticated or request.user.role != 'manager':
        return redirect('login')

    issues = IssueReport.objects.all().order_by('-created_at')
    engineers = CustomUser.objects.filter(role__in=['support_engineer'])
    users = CustomUser.objects.exclude(role='manager')  # 👈 exclude manager from delete list

    total_issues = issues.count()
    unassigned_issues = issues.filter(status='unassigned').count()
    assigned_issues = issues.filter(status='assigned').count()
    done_issues = issues.filter(status='done').count()

    

    context = {
        'issues': issues,
        'engineers': engineers,
        'users': users,  
        'total_issues': total_issues,
        'unassigned_issues': unassigned_issues,
        'assigned_issues': assigned_issues,
        'done_issues': done_issues
    }
    return render(request, 'manager_dashboard.html', context)
    

@csrf_exempt
def issue_reporter_home(request):
    if not request.user.is_authenticated or request.user.role != 'issue_reporter':
        return redirect('login')

    if request.method == 'POST':
        issue_type = request.POST.get('issue_type')
        device_name = request.POST.get('device_name')
        description = request.POST.get('description')
        title = f"{issue_type} issue on {device_name}"

        issue = IssueReport.objects.create(
            reporter=request.user,
            title=title,  
            issue_type=issue_type,
            device_name=device_name,
            description=description,
        )
        messages.success(request, f"Issue submitted! Ticket Number: {issue.ticket_number}. Expected resolution by {issue.expected_resolution_date}.")
        return redirect('issue_reporter_home')

    return render(request, 'issue_reporter.html')


@login_required
def support_engineer_home(request):
    if request.user.role != 'support_engineer':
        return redirect('login')
    print("Current logged in engineer:", request.user.username)
    print("Engineer ID:", request.user.id)

    issues = IssueReport.objects.filter(assigned_engineer=request.user).order_by('-created_at')

    print("Issues assigned to engineer:", issues)

    if request.method == 'POST':
        issue_id = request.POST.get('issue_id')
        new_status = request.POST.get('status')
        try:
            issue = IssueReport.objects.get(id=issue_id, assigned_engineer=request.user)
            issue.status = new_status
            issue.save()
            messages.success(request, "Status updated successfully!")
            return redirect('support_engineer_home')
        except IssueReport.DoesNotExist:
            messages.error(request, "Issue not found or not assigned to you.")

    return render(request, 'support_engineer_home.html', {'assigned_issues': issues})


@csrf_exempt
def update_engineer_status(request, issue_id):
    if request.method == 'POST':
        new_status = request.POST.get('new_status')
        try:
            issue = IssueReport.objects.get(id=issue_id, assigned_engineer=request.user)
            issue.status = new_status
            issue.save()
            return redirect('support_engineer_home')
        except IssueReport.DoesNotExist:
            return HttpResponse("Issue not found", status=404)

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        user = CustomUser.objects.create_user(username=username, password=password, role=role)
        messages.success(request, "Registration successful. Please login.")
        return redirect('login')

    return render(request, 'register.html')

def manager_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'manager':
        return redirect('login')

    issues = IssueReport.objects.all().order_by('-created_at')
    engineers = CustomUser.objects.filter(role__in=['support_engineer'])
    users = CustomUser.objects.exclude(role='manager')  # 👈 exclude manager from delete list

    total_issues = issues.count()
    unassigned_issues = issues.filter(status='unassigned').count()
    assigned_issues = issues.filter(status='assigned').count()
    done_issues = issues.filter(status='done').count()

    print(issues)
    print(engineers)

    context = {
        'issues': issues,
        'engineers': engineers,
        'users': users,  # 👈 Add this
        'total_issues': total_issues,
        'unassigned_issues': unassigned_issues,
        'assigned_issues': assigned_issues,
        'done_issues': done_issues
    }
    return render(request, 'manager_dashboard.html', context)

@csrf_exempt
def assign_engineer(request, issue_id):
    if request.method == 'POST':
        engineer_id = request.POST.get('engineer_id')
        try:
            issue = IssueReport.objects.get(id=issue_id)
            engineer = CustomUser.objects.get(id=engineer_id)
            print("Assigning to:", engineer.username)
            print("Engineer ID:", engineer.id)
            print("Issue ID:", issue.id)
            issue.assigned_engineer = engineer
            issue.status = 'assigned'
            issue.save()
            return redirect('manager_dashboard')
        except IssueReport.DoesNotExist:
            return HttpResponse("Issue not found", status=404)
        except CustomUser.DoesNotExist:
            return HttpResponse("Engineer not found", status=404)
        
@csrf_exempt
def delete_issue(request, issue_id):
    if request.method == 'POST':
        try:
            issue = IssueReport.objects.get(id=issue_id)
            issue.delete()
            return redirect('manager_dashboard')
        except IssueReport.DoesNotExist:
            return HttpResponse("Issue not found", status=404)        

@csrf_exempt
def update_status_done(request, issue_id):
    if request.method == 'POST':
        try:
            issue = IssueReport.objects.get(id=issue_id)
            issue.status = 'done'
            issue.save()
            return redirect('manager_dashboard')
        except IssueReport.DoesNotExist:
            return HttpResponse("Issue not found", status=404)
        

@csrf_exempt
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user = CustomUser.objects.get(id=user_id)
            user.delete()
            return HttpResponse("User deleted successfully")
        except CustomUser.DoesNotExist:
            return HttpResponse("User not found", status=404)
        
def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role')
        new_password = request.POST.get('new_password')

        try:
            user = CustomUser.objects.get(username=username, role=role)
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password updated successfully. Please login again.")
            return redirect('login')
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found with given role and username.")

    return render(request, 'forgot_password.html')
