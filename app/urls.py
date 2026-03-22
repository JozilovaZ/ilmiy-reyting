from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),

    # Ilmiy ishlar
    path('works/add/', views.add_work_view, name='add_work'),
    path('works/my/', views.my_works_view, name='my_works'),
    path('works/edit/<int:pk>/', views.edit_work_view, name='edit_work'),
    path('works/delete/<int:pk>/', views.delete_work_view, name='delete_work'),

    # Katta o'qituvchi - boshqaruv
    path('works/all/', views.all_works_view, name='all_works'),
    path('works/approve/<int:pk>/', views.approve_work_view, name='approve_work'),
    path('works/reject/<int:pk>/', views.reject_work_view, name='reject_work'),

    # Reyting va statistika
    path('rating/', views.rating_view, name='rating'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('teacher/<int:pk>/', views.teacher_detail_view, name='teacher_detail'),

    # Bildirishnomalar
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/read/<int:pk>/', views.mark_notification_read, name='mark_read'),
    path('notifications/read-all/', views.mark_all_read, name='mark_all_read'),

    # Boshqaruv
    path('manage/work-types/', views.manage_work_types_view, name='manage_work_types'),
    path('manage/deadlines/', views.deadlines_view, name='deadlines'),
    path('manage/activity-log/', views.activity_log_view, name='activity_log'),

    # Export
    path('export/excel/', views.export_excel_view, name='export_excel'),
    path('export/pdf/', views.export_pdf_view, name='export_pdf'),
]
