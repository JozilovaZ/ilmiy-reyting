from django.contrib import admin
from .models import User, Kafedra, Teacher, WorkType, ScientificWork, Notification, Deadline, ActivityLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'role', 'email']
    list_filter = ['role']
    search_fields = ['username', 'first_name', 'last_name']


@admin.register(Kafedra)
class KafedraAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'kafedra', 'position', 'degree', 'experience_years']
    list_filter = ['kafedra', 'degree']
    search_fields = ['user__first_name', 'user__last_name']


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'score']
    list_editable = ['score']


@admin.register(ScientificWork)
class ScientificWorkAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'work_type', 'date', 'status']
    list_filter = ['status', 'work_type']
    search_fields = ['title', 'teacher__user__first_name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'notif_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'notif_type']


@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
    list_display = ['title', 'due_date', 'is_active']
    list_filter = ['is_active']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'details', 'created_at']
    list_filter = ['action']
    search_fields = ['user__username', 'details']
