from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid
from datetime import timedelta, date

# Custom user manager
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, role=None):
        if not username:
            raise ValueError('Users must have a username')
        user = self.model(username=username, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

# Custom user model
class CustomUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('issue_reporter', 'Issue Reporter'),
        ('support_engineer', 'Support Engineer'),
    ]
    username = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    USERNAME_FIELD = 'username'
    objects = CustomUserManager()

    def __str__(self):
        return self.username

# ✅ Merged and cleaned IssueReport model
class IssueReport(models.Model):
    ISSUE_TYPE_CHOICES = [
        ('software', 'Software'),
        ('hardware', 'Hardware'),
    ]
    STATUS_CHOICES = [
        ('unassigned', 'Unassigned'),
        ('assigned', 'Assigned'),
        ('inprogress', 'In Progress'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPE_CHOICES)
    device_name = models.CharField(max_length=100)
    reporter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reported_issues')
    assigned_engineer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unassigned')
    ticket_number = models.CharField(max_length=100, editable=False, null=True, blank=True, unique=True)
    expected_resolution_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = "TKT-" + str(uuid.uuid4().hex[:8]).upper()

        if not self.expected_resolution_date:
            if self.issue_type == 'software':
                self.expected_resolution_date = date.today() + timedelta(days=1)
            elif self.issue_type == 'hardware':
                self.expected_resolution_date = date.today() + timedelta(days=2)

        super(IssueReport, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.device_name}"
