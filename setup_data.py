import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import User, Kafedra, Teacher, WorkType, ScientificWork, Deadline
from datetime import date

# Superuser (Katta o'qituvchi)
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        password='admin123',
        first_name='Ahror',
        last_name='Aliyev',
        email='admin@example.com',
        role='katta_oqituvchi'
    )
    Teacher.objects.create(
        user=admin, position="Katta o'qituvchi",
        degree='dsc', experience_years=20
    )
    print("Katta o'qituvchi yaratildi: admin / admin123")

# Kafedralar
kafedralar = [
    "Informatika va axborot texnologiyalari",
    "Matematika",
    "Fizika",
    "Iqtisodiyot",
]
for k in kafedralar:
    Kafedra.objects.get_or_create(name=k)
print(f"{len(kafedralar)} ta kafedra yaratildi")

# Ish turlari va ballar
work_types = [
    ("Ilmiy maqola (xalqaro)", 15),
    ("Ilmiy maqola (respublika)", 10),
    ("Kitob", 30),
    ("Darslik", 25),
    ("Konferensiya (xalqaro)", 8),
    ("Konferensiya (respublika)", 5),
    ("Patent", 20),
    ("Metodik qo'llanma", 12),
    ("Dissertatsiya", 40),
    ("Sertifikat", 3),
]
for name, score in work_types:
    WorkType.objects.get_or_create(name=name, defaults={'score': score})
print(f"{len(work_types)} ta ish turi yaratildi")

# Namuna o'qituvchilar (kichik o'qituvchilar)
kafedra1 = Kafedra.objects.first()
teachers_data = [
    ("teacher1", "Karimova", "Kamola", "Dotsent", "dotsent", 10),
    ("teacher2", "Rahimov", "Rustam", "O'qituvchi", "phd", 8),
    ("teacher3", "Saidova", "Sabohat", "O'qituvchi", "none", 3),
    ("teacher4", "Toshmatov", "Jasur", "O'qituvchi", "phd", 5),
]
for uname, last, first, position, degree, exp in teachers_data:
    if not User.objects.filter(username=uname).exists():
        user = User.objects.create_user(
            username=uname, password='1234', first_name=first,
            last_name=last, role='oqituvchi'
        )
        Teacher.objects.create(
            user=user, kafedra=kafedra1, position=position,
            degree=degree, experience_years=exp
        )
print("Namuna o'qituvchilar yaratildi")

# Namuna ilmiy ishlar
wt_maqola = WorkType.objects.filter(name__icontains="xalqaro").first()
wt_kitob = WorkType.objects.get(name="Kitob")
wt_konf = WorkType.objects.filter(name__icontains="Konferensiya (respublika)").first()
wt_patent = WorkType.objects.get(name="Patent")

t1 = Teacher.objects.filter(user__username='teacher1').first()
t2 = Teacher.objects.filter(user__username='teacher2').first()
t3 = Teacher.objects.filter(user__username='teacher3').first()

if t1 and not ScientificWork.objects.filter(teacher=t1).exists():
    ScientificWork.objects.create(teacher=t1, work_type=wt_maqola, title="Sun'iy intellekt asosida ta'lim tizimi", date=date(2025, 3, 15), status='approved')
    ScientificWork.objects.create(teacher=t1, work_type=wt_kitob, title="Python dasturlash tili", date=date(2025, 5, 10), status='approved')
    ScientificWork.objects.create(teacher=t1, work_type=wt_konf, title="Raqamli ta'lim konferensiyasi", date=date(2025, 9, 20), status='pending')

if t2 and not ScientificWork.objects.filter(teacher=t2).exists():
    ScientificWork.objects.create(teacher=t2, work_type=wt_maqola, title="Ma'lumotlar bazasi optimizatsiyasi", date=date(2025, 4, 5), status='approved')
    ScientificWork.objects.create(teacher=t2, work_type=wt_patent, title="Axborot xavfsizligi tizimi", date=date(2025, 7, 12), status='pending')

if t3 and not ScientificWork.objects.filter(teacher=t3).exists():
    ScientificWork.objects.create(teacher=t3, work_type=wt_konf, title="Zamonaviy pedagogika usullari", date=date(2025, 8, 20), status='pending')

# Namuna muddat
Deadline.objects.get_or_create(
    title="Oylik hisobot topshirish",
    defaults={
        'description': "Barcha o'qituvchilar oylik ilmiy ishlar hisobotini topshirishi kerak",
        'due_date': date(2026, 3, 31),
        'is_active': True,
    }
)

print("Namuna ilmiy ishlar va muddatlar yaratildi")
print("\n=== TAYYOR ===")
print("Katta o'qituvchi: admin / admin123")
print("O'qituvchilar: teacher1 / 1234, teacher2 / 1234, teacher3 / 1234, teacher4 / 1234")
print("\nRollar:")
print("  - Katta o'qituvchi (admin): ishlarni tasdiqlaydi, ballarni sozlaydi, statistikani ko'radi")
print("  - O'qituvchi: ish qo'shadi, reytingni ko'radi")
