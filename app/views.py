from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from datetime import datetime, date

from .models import User, Teacher, ScientificWork, WorkType, Notification, Kafedra, Deadline, ActivityLog
from .forms import (RegisterForm, UserUpdateForm, TeacherForm, ScientificWorkForm,
                    PasswordChangeCustomForm, WorkTypeForm, DeadlineForm, RejectForm)


def log_activity(user, action, details=''):
    ActivityLog.objects.create(user=user, action=action, details=details)


def notify_user(user, message, notif_type='info'):
    Notification.objects.create(user=user, message=message, notif_type=notif_type)


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'oqituvchi'
            user.save()
            Teacher.objects.create(user=user, position="O'qituvchi")
            login(request, user)
            messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz!")
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}

    if hasattr(user, 'teacher'):
        teacher = user.teacher
        works = teacher.works.all()
        context['teacher'] = teacher
        context['total_score'] = teacher.total_score()
        context['works_count'] = works.count()
        context['pending_count'] = works.filter(status='pending').count()
        context['approved_count'] = works.filter(status='approved').count()
        context['rejected_count'] = works.filter(status='rejected').count()
        context['recent_works'] = works[:5]

    if user.is_katta():
        context['all_teachers_count'] = Teacher.objects.count()
        context['all_works_count'] = ScientificWork.objects.count()
        context['pending_works'] = ScientificWork.objects.filter(status='pending').count()
        context['recent_activities'] = ActivityLog.objects.all()[:10]

    # Deadlinelar
    active_deadlines = Deadline.objects.filter(is_active=True)
    context['deadlines'] = active_deadlines
    overdue_deadlines = [d for d in active_deadlines if d.is_overdue]
    context['overdue_deadlines'] = overdue_deadlines

    # Bildirishnomalar
    notifications = user.notifications.filter(is_read=False)[:5]
    context['notifications'] = notifications
    context['unread_count'] = user.notifications.filter(is_read=False).count()

    # TOP 3
    top3 = list(Teacher.objects.annotate(
        score=Coalesce(Sum('works__work_type__score', filter=Q(works__status='approved')), Value(0))
    ).filter(score__gt=0).order_by('-score')[:3])
    context['top3'] = top3

    return render(request, 'dashboard.html', context)


@login_required
def profile_view(request):
    user = request.user
    teacher = getattr(user, 'teacher', None)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        t_form = TeacherForm(request.POST, instance=teacher) if teacher else None

        if u_form.is_valid() and (t_form is None or t_form.is_valid()):
            u_form.save()
            if t_form:
                t_form.save()
            log_activity(user, 'profile_updated', "Profil ma'lumotlari yangilandi")
            messages.success(request, "Profil yangilandi!")
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=user)
        t_form = TeacherForm(instance=teacher) if teacher else None

    context = {
        'u_form': u_form,
        't_form': t_form,
        'teacher': teacher,
    }

    if teacher:
        works = teacher.works.all()
        context['total_score'] = teacher.total_score()
        context['works_count'] = works.count()
        context['approved_count'] = works.filter(status='approved').count()
        context['pending_count'] = works.filter(status='pending').count()
        context['rejected_count'] = works.filter(status='rejected').count()

        # Reytingdagi o'rni
        all_teachers = Teacher.objects.annotate(
            score=Coalesce(Sum('works__work_type__score', filter=Q(works__status='approved')), Value(0))
        ).order_by('-score')
        rank = 1
        for t in all_teachers:
            if t.pk == teacher.pk:
                break
            rank += 1
        context['rank'] = rank
        context['total_teachers'] = all_teachers.count()

    return render(request, 'profile.html', context)


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.POST)
        if form.is_valid():
            old_pw = form.cleaned_data['old_password']
            new_pw1 = form.cleaned_data['new_password1']
            new_pw2 = form.cleaned_data['new_password2']

            if not request.user.check_password(old_pw):
                messages.error(request, "Eski parol noto'g'ri!")
            elif new_pw1 != new_pw2:
                messages.error(request, "Yangi parollar mos kelmadi!")
            else:
                request.user.set_password(new_pw1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Parol muvaffaqiyatli o'zgartirildi!")
                return redirect('profile')
    else:
        form = PasswordChangeCustomForm()
    return render(request, 'change_password.html', {'form': form})


# ==================== ILMIY ISHLAR ====================

@login_required
def add_work_view(request):
    teacher = getattr(request.user, 'teacher', None)
    if not teacher:
        messages.error(request, "Sizning o'qituvchi profilingiz topilmadi! Administrator bilan bog'laning.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ScientificWorkForm(request.POST, request.FILES)
        if form.is_valid():
            work = form.save(commit=False)
            work.teacher = teacher
            work.status = 'pending'
            work.save()

            log_activity(request.user, 'work_added', f"Yan"
                                                     f""
                                                     f"gi ish: {work.title}")

            # Katta o'qituvchiga bildirishnoma
            katta = User.objects.filter(role='katta_oqituvchi').first()
            if katta:
                notify_user(katta,
                    f"{teacher.user.get_full_name()} yangi ilmiy ish qo'shdi: \"{work.title}\". Tasdiqlash kutilmoqda.",
                    'info')

            messages.success(request, "Ilmiy ish yuborildi! Katta o'qituvchi tasdiqlashini kuting.")
            return redirect('my_works')
    else:
        form = ScientificWorkForm()
    return render(request, 'works/add_work.html', {'form': form})


@login_required
def my_works_view(request):
    teacher = getattr(request.user, 'teacher', None)
    if not teacher:
        messages.error(request, "Sizning o'qituvchi profilingiz topilmadi! Administrator bilan bog'laning.")
        return redirect('dashboard')
    works = teacher.works.all()

    work_type = request.GET.get('type')
    year = request.GET.get('year')
    status = request.GET.get('status')
    search = request.GET.get('search')

    if work_type:
        works = works.filter(work_type_id=work_type)
    if year:
        works = works.filter(date__year=year)
    if status:
        works = works.filter(status=status)
    if search:
        works = works.filter(Q(title__icontains=search))

    work_types = WorkType.objects.all()
    years = teacher.works.dates('date', 'year')

    return render(request, 'works/my_works.html', {
        'works': works,
        'work_types': work_types,
        'years': years,
        'teacher': teacher,
    })


@login_required
def edit_work_view(request, pk):
    work = get_object_or_404(ScientificWork, pk=pk, teacher__user=request.user)

    if work.status == 'approved':
        messages.error(request, "Tasdiqlangan ishni tahrirlash mumkin emas!")
        return redirect('my_works')

    if request.method == 'POST':
        form = ScientificWorkForm(request.POST, request.FILES, instance=work)
        if form.is_valid():
            work = form.save(commit=False)
            work.status = 'pending'
            work.save()
            log_activity(request.user, 'work_edited', f"Ish tahrirlandi: {work.title}")
            messages.success(request, "Ilmiy ish yangilandi va qayta tekshiruvga yuborildi!")
            return redirect('my_works')
    else:
        form = ScientificWorkForm(instance=work)
    return render(request, 'works/edit_work.html', {'form': form, 'work': work})


@login_required
def delete_work_view(request, pk):
    work = get_object_or_404(ScientificWork, pk=pk, teacher__user=request.user)
    if work.status == 'approved':
        messages.error(request, "Tasdiqlangan ishni o'chirish mumkin emas!")
        return redirect('my_works')
    if request.method == 'POST':
        title = work.title
        work.delete()
        log_activity(request.user, 'work_deleted', f"Ish o'chirildi: {title}")
        messages.success(request, "Ilmiy ish o'chirildi!")
    return redirect('my_works')


# ==================== KATTA O'QITUVCHI - BOSHQARUV ====================

@login_required
def all_works_view(request):
    if not request.user.is_katta():
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    works = ScientificWork.objects.select_related('teacher__user', 'work_type').all()

    status = request.GET.get('status')
    work_type = request.GET.get('type')
    search = request.GET.get('search')
    teacher_id = request.GET.get('teacher')

    if status:
        works = works.filter(status=status)
    if work_type:
        works = works.filter(work_type_id=work_type)
    if teacher_id:
        works = works.filter(teacher_id=teacher_id)
    if search:
        works = works.filter(
            Q(title__icontains=search) | Q(teacher__user__first_name__icontains=search) |
            Q(teacher__user__last_name__icontains=search)
        )

    work_types = WorkType.objects.all()
    teachers = Teacher.objects.all()

    return render(request, 'works/all_works.html', {
        'works': works,
        'work_types': work_types,
        'teachers': teachers,
    })


@login_required
def approve_work_view(request, pk):
    if not request.user.is_katta():
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    work = get_object_or_404(ScientificWork, pk=pk)
    work.status = 'approved'
    work.save()

    log_activity(request.user, 'work_approved', f"Tasdiqlandi: {work.title} ({work.teacher})")

    notify_user(work.teacher.user,
        f"Sizning \"{work.title}\" ilmiy ishingiz tasdiqlandi! +{work.work_type.score} ball",
        'approved')

    messages.success(request, "Ilmiy ish tasdiqlandi!")
    return redirect('all_works')


@login_required
def reject_work_view(request, pk):
    if not request.user.is_katta():
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    work = get_object_or_404(ScientificWork, pk=pk)

    if request.method == 'POST':
        form = RejectForm(request.POST)
        if form.is_valid():
            work.status = 'rejected'
            work.reject_reason = form.cleaned_data['reject_reason']
            work.save()

            log_activity(request.user, 'work_rejected', f"Rad etildi: {work.title} - Sabab: {work.reject_reason}")

            notify_user(work.teacher.user,
                f"Sizning \"{work.title}\" ilmiy ishingiz rad etildi. Sabab: {work.reject_reason}",
                'rejected')

            messages.success(request, "Ilmiy ish rad etildi!")
            return redirect('all_works')
    else:
        form = RejectForm()

    return render(request, 'works/reject_work.html', {'form': form, 'work': work})


# ==================== REYTING ====================

@login_required
def rating_view(request):
    teachers = Teacher.objects.annotate(
        score=Sum('works__work_type__score', filter=Q(works__status='approved'))
    ).order_by('-score')

    kafedra_id = request.GET.get('kafedra')
    year = request.GET.get('year')

    if kafedra_id:
        teachers = teachers.filter(kafedra_id=kafedra_id)
    if year:
        teachers = Teacher.objects.annotate(
            score=Sum('works__work_type__score', filter=Q(works__status='approved', works__date__year=year))
        ).order_by('-score')
        if kafedra_id:
            teachers = teachers.filter(kafedra_id=kafedra_id)

    kafedralar = Kafedra.objects.all()

    # Diagrammalar uchun ma'lumotlar
    top10 = list(teachers[:10])
    chart_names = [t.user.get_full_name() or t.user.username for t in top10]
    chart_scores = [t.score or 0 for t in top10]

    # Kafedra bo'yicha ball taqsimoti
    kafedra_chart = []
    score_filter = Q(works__status='approved')
    if year:
        score_filter &= Q(works__date__year=year)
    for k in kafedralar:
        k_teachers = Teacher.objects.filter(kafedra=k)
        if kafedra_id:
            continue
        total = k_teachers.aggregate(
            total=Coalesce(Sum('works__work_type__score', filter=score_filter), Value(0))
        )['total']
        if total > 0:
            kafedra_chart.append({'name': k.name, 'score': total})

    kafedra_names = [k['name'] for k in kafedra_chart]
    kafedra_scores = [k['score'] for k in kafedra_chart]

    # Ish turlari bo'yicha taqsimot
    work_type_filter = Q(scientificwork__status='approved')
    if year:
        work_type_filter &= Q(scientificwork__date__year=year)
    if kafedra_id:
        work_type_filter &= Q(scientificwork__teacher__kafedra_id=kafedra_id)

    work_types_data = WorkType.objects.annotate(
        count=Count('scientificwork', filter=work_type_filter)
    ).filter(count__gt=0)
    wt_names = [wt.name for wt in work_types_data]
    wt_counts = [wt.count for wt in work_types_data]

    import json
    return render(request, 'rating.html', {
        'teachers': teachers,
        'kafedralar': kafedralar,
        'chart_names': json.dumps(chart_names),
        'chart_scores': json.dumps(chart_scores),
        'kafedra_names': json.dumps(kafedra_names),
        'kafedra_scores': json.dumps(kafedra_scores),
        'wt_names': json.dumps(wt_names),
        'wt_counts': json.dumps(wt_counts),
    })


# ==================== STATISTIKA ====================

@login_required
def statistics_view(request):
    current_year = datetime.now().year
    work_types = WorkType.objects.all()

    stats = []
    for wt in work_types:
        count = ScientificWork.objects.filter(work_type=wt, status='approved').count()
        stats.append({'name': wt.name, 'count': count, 'score': wt.score})

    monthly_stats = []
    for month in range(1, 13):
        count = ScientificWork.objects.filter(
            date__year=current_year, date__month=month, status='approved'
        ).count()
        monthly_stats.append({'month': month, 'count': count})

    top_teachers = Teacher.objects.annotate(
        score=Sum('works__work_type__score', filter=Q(works__status='approved'))
    ).order_by('-score')[:10]

    # Kafedra statistikasi
    kafedra_stats = []
    for k in Kafedra.objects.all():
        teacher_count = Teacher.objects.filter(kafedra=k).count()
        works_count = ScientificWork.objects.filter(teacher__kafedra=k, status='approved').count()
        total_score = ScientificWork.objects.filter(
            teacher__kafedra=k, status='approved'
        ).aggregate(total=Sum('work_type__score'))['total'] or 0
        kafedra_stats.append({
            'name': k.name, 'teachers': teacher_count,
            'works': works_count, 'score': total_score
        })

    return render(request, 'statistics.html', {
        'stats': stats,
        'monthly_stats': monthly_stats,
        'top_teachers': top_teachers,
        'current_year': current_year,
        'kafedra_stats': kafedra_stats,
    })


# ==================== BILDIRISHNOMALAR ====================

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    return render(request, 'notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')


@login_required
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications')


# ==================== TEACHER DETAIL ====================

@login_required
def teacher_detail_view(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    works = teacher.works.filter(status='approved')
    return render(request, 'teacher_detail.html', {
        'teacher': teacher,
        'works': works,
        'total_score': teacher.total_score(),
    })


# ==================== DYNAMIC SCORING ====================

@login_required
def manage_work_types_view(request):
    if not request.user.is_katta():
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    work_types = WorkType.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            form = WorkTypeForm(request.POST)
            if form.is_valid():
                form.save()
                log_activity(request.user, 'score_changed', f"Yangi ish turi qo'shildi: {form.cleaned_data['name']}")
                messages.success(request, "Yangi ish turi qo'shildi!")
                return redirect('manage_work_types')

        elif action == 'update':
            wt_id = request.POST.get('wt_id')
            wt = get_object_or_404(WorkType, pk=wt_id)
            old_score = wt.score
            form = WorkTypeForm(request.POST, instance=wt)
            if form.is_valid():
                form.save()
                log_activity(request.user, 'score_changed',
                    f"{wt.name}: {old_score} → {wt.score} ball")
                messages.success(request, f"'{wt.name}' yangilandi!")
                return redirect('manage_work_types')

        elif action == 'delete':
            wt_id = request.POST.get('wt_id')
            wt = get_object_or_404(WorkType, pk=wt_id)
            name = wt.name
            wt.delete()
            log_activity(request.user, 'score_changed', f"Ish turi o'chirildi: {name}")
            messages.success(request, f"'{name}' o'chirildi!")
            return redirect('manage_work_types')

    add_form = WorkTypeForm()
    return render(request, 'manage_work_types.html', {
        'work_types': work_types,
        'add_form': add_form,
    })


# ==================== DEADLINELAR ====================

@login_required
def deadlines_view(request):
    deadlines = Deadline.objects.all()

    if request.user.is_katta() and request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            form = DeadlineForm(request.POST)
            if form.is_valid():
                deadline = form.save()
                # Barcha o'qituvchilarga bildirishnoma
                for u in User.objects.filter(role='oqituvchi'):
                    notify_user(u,
                        f"Yangi muddat belgilandi: \"{deadline.title}\" - {deadline.due_date.strftime('%d.%m.%Y')} gacha",
                        'deadline')
                messages.success(request, "Yangi muddat belgilandi!")
                return redirect('deadlines')

        elif action == 'toggle':
            dl_id = request.POST.get('dl_id')
            dl = get_object_or_404(Deadline, pk=dl_id)
            dl.is_active = not dl.is_active
            dl.save()
            return redirect('deadlines')

        elif action == 'delete':
            dl_id = request.POST.get('dl_id')
            dl = get_object_or_404(Deadline, pk=dl_id)
            dl.delete()
            messages.success(request, "Muddat o'chirildi!")
            return redirect('deadlines')

    add_form = DeadlineForm()
    return render(request, 'deadlines.html', {
        'deadlines': deadlines,
        'add_form': add_form,
    })


# ==================== ACTIVITY HISTORY ====================

@login_required
def activity_log_view(request):
    if not request.user.is_katta():
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    logs = ActivityLog.objects.select_related('user').all()

    user_id = request.GET.get('user')
    action = request.GET.get('action')

    if user_id:
        logs = logs.filter(user_id=user_id)
    if action:
        logs = logs.filter(action=action)

    users = User.objects.all()

    return render(request, 'activity_log.html', {
        'logs': logs[:100],
        'users': users,
    })


# ==================== EXPORT ====================

@login_required
def export_excel_view(request):
    if not request.user.is_katta():
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reyting"

    headers = ['#', "O'qituvchi", 'Kafedra', 'Lavozimi', 'Ilmiy darajasi', 'Umumiy ball']
    ws.append(headers)

    teachers = Teacher.objects.annotate(
        score=Sum('works__work_type__score', filter=Q(works__status='approved'))
    ).order_by('-score')

    for i, t in enumerate(teachers, 1):
        ws.append([
            i,
            str(t.user),
            str(t.kafedra) if t.kafedra else '-',
            t.position,
            t.get_degree_display(),
            t.score or 0,
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reyting.xlsx"'
    wb.save(response)
    return response


@login_required
def export_pdf_view(request):
    if not request.user.is_katta():
        messages.error(request, "Sizda ruxsat yo'q!")
        return redirect('dashboard')

    teachers = Teacher.objects.annotate(
        score=Sum('works__work_type__score', filter=Q(works__status='approved'))
    ).order_by('-score')

    return render(request, 'export_pdf.html', {'teachers': teachers})
