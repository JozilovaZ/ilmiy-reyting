from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.core.exceptions import ValidationError
import os


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError("Faqat PDF formatdagi fayllar qabul qilinadi!")


def validate_file_size(value):
    limit = 10 * 1024 * 1024  # 10 MB
    if value.size > limit:
        raise ValidationError("Fayl hajmi 10 MB dan oshmasligi kerak!")


class User(AbstractUser):
    ROLE_CHOICES = (
        ('katta_oqituvchi', "Katta o'qituvchi"),
        ('oqituvchi', "O'qituvchi"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='oqituvchi')
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telegram Chat ID')

    def __str__(self):
        return self.get_full_name() or self.username

    def is_katta(self):
        return self.role == 'katta_oqituvchi'


class Kafedra(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Kafedra'
        verbose_name_plural = 'Kafedralar'


class Teacher(models.Model):
    DEGREE_CHOICES = (
        ('none', 'Ilmiy darajasi yo\'q'),
        ('phd', 'PhD'),
        ('dsc', 'DSc'),
        ('professor', 'Professor'),
        ('dotsent', 'Dotsent'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    kafedra = models.ForeignKey(Kafedra, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=255, verbose_name='Lavozimi')
    experience_years = models.PositiveIntegerField(default=0, verbose_name='Ish staji (yil)')
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES, default='none', verbose_name='Ilmiy darajasi')
    bio = models.TextField(blank=True, verbose_name='Qo\'shimcha ma\'lumot')

    def __str__(self):
        return str(self.user)

    def total_score(self):
        result = self.works.filter(status='approved').aggregate(total=Sum('work_type__score'))
        return result['total'] or 0

    class Meta:
        verbose_name = "O'qituvchi"
        verbose_name_plural = "O'qituvchilar"


class WorkType(models.Model):
    name = models.CharField(max_length=255, verbose_name='Ish turi nomi')
    score = models.PositiveIntegerField(default=0, verbose_name='Ball')

    def __str__(self):
        return f"{self.name} ({self.score} ball)"

    class Meta:
        verbose_name = 'Ish turi'
        verbose_name_plural = 'Ish turlari'


class Deadline(models.Model):
    title = models.CharField(max_length=255, verbose_name='Nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    due_date = models.DateField(verbose_name='Muddat')
    is_active = models.BooleanField(default=True, verbose_name='Faolmi')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.due_date}"

    @property
    def is_overdue(self):
        from datetime import date
        return date.today() > self.due_date and self.is_active

    @property
    def days_left(self):
        from datetime import date
        delta = self.due_date - date.today()
        return delta.days

    class Meta:
        verbose_name = 'Muddat'
        verbose_name_plural = 'Muddatlar'
        ordering = ['due_date']


class ScientificWork(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Rad etilgan'),
    )
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='works')
    work_type = models.ForeignKey(WorkType, on_delete=models.CASCADE, verbose_name='Ish turi')
    title = models.CharField(max_length=500, verbose_name='Nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    date = models.DateField(verbose_name='Sana')
    file = models.FileField(
        upload_to='works/', blank=True, null=True, verbose_name='Fayl (PDF)',
        validators=[validate_file_extension, validate_file_size]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reject_reason = models.TextField(blank=True, verbose_name='Rad etish sababi')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.teacher} -{self.title} -{self.work_type} -{self.date}"

    class Meta:
        verbose_name = 'Ilmiy ish'
        verbose_name_plural = 'Ilmiy ishlar'
        ordering = ['-created_at']


class Notification(models.Model):
    NOTIF_TYPES = (
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Rad etilgan'),
        ('info', 'Ma\'lumot'),
        ('deadline', 'Muddat'),
        ('rating', 'Reyting'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:50]

    class Meta:
        ordering = ['-created_at']


class ActivityLog(models.Model):
    ACTION_CHOICES = (
        ('work_added', 'Ish qo\'shildi'),
        ('work_edited', 'Ish tahrirlandi'),
        ('work_deleted', 'Ish o\'chirildi'),
        ('work_approved', 'Ish tasdiqlandi'),
        ('work_rejected', 'Ish rad etildi'),
        ('profile_updated', 'Profil yangilandi'),
        ('login', 'Tizimga kirdi'),
        ('score_changed', 'Ball o\'zgartirildi'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.get_action_display()}"

    class Meta:
        verbose_name = 'Faoliyat tarixi'
        verbose_name_plural = 'Faoliyat tarixi'
        ordering = ['-created_at']
