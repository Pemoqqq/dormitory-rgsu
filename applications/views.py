from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from applications.models import Application, Document, Contract
from applications.forms import ApplicationForm, DocumentUploadForm
from applications.services.rating import calculate_rating, update_queue_positions
from dorms.models import Room, Dormitory
from users.models import User
import json


# ============================================================================
# ПРЕДСТАВЛЕНИЯ ДЛЯ СТУДЕНТА (АБИТУРИЕНТА)
# ============================================================================

@login_required
def create_application(request):
    """
    Создание новой заявки на заселение.
    Студент может иметь только одну активную заявку.
    """
    # Проверяем, нет ли уже активной заявки
    active_app = Application.objects.filter(
        student=request.user,
        status__in=['draft', 'submitted', 'under_review', 'approved', 'assigned']
    ).first()
    
    if active_app:
        messages.warning(request, 'У вас уже есть активная заявка. Перенаправляем на страницу статуса.')
        return redirect('applications:status')

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            # 1. Сохраняем заявку
            app = form.save(commit=False)
            app.student = request.user
            app.status = 'submitted'
            app.save()

            # 2. Считаем рейтинг
            calculate_rating(app)
            app.save(update_fields=['rating_score'])
            
            # 3. Обновляем очередь
            update_queue_positions()
            
            messages.success(request, 'Заявка успешно создана и отправлена на рассмотрение!')
            return redirect('applications:upload')
    else:
        form = ApplicationForm()

    return render(request, 'applications/create_application.html', {'form': form})


@login_required
def upload_documents(request):
    """
    Загрузка документов для заявки.
    Пошаговая загрузка с валидацией.
    """
    app = get_object_or_404(
        Application, 
        student=request.user, 
        status__in=['submitted', 'under_review', 'approved', 'assigned']
    )

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Проверяем, не загружен ли уже этот тип документа
            existing_doc = Document.objects.filter(
                application=app, 
                doc_type=form.cleaned_data['doc_type']
            ).first()
            
            if existing_doc:
                messages.warning(request, 'Этот тип документа уже загружен. Удалите старый файл перед загрузкой нового.')
            else:
                doc = form.save(commit=False)
                doc.application = app
                doc.save()
                messages.success(request, f'Документ «{doc.get_doc_type_display()}» успешно загружен.')
            
            return redirect('applications:upload')
    else:
        form = DocumentUploadForm()

    documents = Document.objects.filter(application=app).order_by('doc_type')
    
    # Считаем, сколько документов загружено
    required_docs_count = len(Document.DOC_TYPE_CHOICES)
    uploaded_docs_count = documents.count()
    progress_percent = int((uploaded_docs_count / required_docs_count) * 100) if required_docs_count > 0 else 0

    return render(request, 'applications/upload_documents.html', {
        'form': form,
        'documents': documents,
        'app': app,
        'progress_percent': progress_percent,
        'required_docs_count': required_docs_count,
        'uploaded_docs_count': uploaded_docs_count,
    })


@login_required
def application_status(request):
    """
    Просмотр статуса заявки, рейтинга и позиции в очереди.
    """
    app = Application.objects.filter(student=request.user).order_by('-created_at').first()
    if not app:
        messages.info(request, 'У вас пока нет заявок. Создайте новую заявку.')
        return redirect('applications:create')

    # Получаем документы
    documents = Document.objects.filter(application=app)
    verified_docs = documents.filter(is_verified=True).count()
    
    # Если заявка одобрена и назначена комната
    contract = None
    if hasattr(app, 'contract'):
        contract = app.contract

    return render(request, 'applications/status.html', {
        'app': app,
        'documents': documents,
        'verified_docs': verified_docs,
        'contract': contract,
    })


@login_required
def cancel_application(request, application_id):
    """
    Отмена заявки студентом (только если она в статусе draft или submitted).
    """
    app = get_object_or_404(Application, id=application_id, student=request.user)
    
    if app.status in ['draft', 'submitted']:
        app.status = 'draft'  # или можно добавить статус 'cancelled'
        app.save()
        messages.success(request, 'Заявка отменена.')
        return redirect('applications:create')
    else:
        messages.error(request, 'Невозможно отменить заявку в текущем статусе.')
        return redirect('applications:status')


# ============================================================================
# ПРЕДСТАВЛЕНИЯ ДЛЯ АДМИНИСТРАТОРА
# ============================================================================

@staff_member_required
def admin_application_list(request):
    """
    Список всех заявок для администратора.
    Фильтрация, поиск, сортировка.
    """
    applications = Application.objects.select_related('student', 'assigned_room__dormitory').all()
    
    # Фильтры
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Поиск по ФИО
    search_query = request.GET.get('search')
    if search_query:
        applications = applications.filter(
            Q(student__last_name__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__patronymic__icontains=search_query)
        )
    
    # Сортировка
    sort_by = request.GET.get('sort', '-rating_score')
    applications = applications.order_by(sort_by)
    
    # Пагинация
    paginator = Paginator(applications, 50)  # 50 заявок на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'statuses': Application.STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'applications/admin_application_list.html', context)


@staff_member_required
def admin_application_detail(request, application_id):
    """
    Детальный просмотр заявки администратором.
    """
    app = get_object_or_404(
        Application.objects.select_related('student', 'assigned_room__dormitory'),
        id=application_id
    )
    documents = Document.objects.filter(application=app)
    
    return render(request, 'applications/admin_application_detail.html', {
        'app': app,
        'documents': documents,
    })


@staff_member_required
@require_http_methods(["POST"])
def admin_verify_document(request, document_id):
    """
    Верификация документа администратором.
    """
    doc = get_object_or_404(Document, id=document_id)
    is_verified = request.POST.get('is_verified') == 'true'
    comment = request.POST.get('comment', '')
    
    doc.is_verified = is_verified
    doc.verified_by = request.user
    doc.comment = comment
    doc.save()
    
    if is_verified:
        messages.success(request, f'Документ «{doc.get_doc_type_display()}» подтверждён.')
    else:
        messages.warning(request, f'Документ «{doc.get_doc_type_display()}» отклонён.')
    
    return JsonResponse({'status': 'ok'})


@staff_member_required
@require_http_methods(["POST"])
def admin_update_application_status(request, application_id):
    """
    Изменение статуса заявки администратором.
    """
    app = get_object_or_404(Application, id=application_id)
    new_status = request.POST.get('status')
    admin_comment = request.POST.get('admin_comment', '')
    
    if new_status in dict(Application.STATUS_CHOICES):
        app.status = new_status
        app.admin_comment = admin_comment
        app.save()
        messages.success(request, f'Статус заявки изменён на «{app.get_status_display()}».')
    else:
        messages.error(request, 'Неверный статус.')
    
    return redirect('applications:admin_application_detail', application_id=application_id)


@staff_member_required
@require_http_methods(["POST"])
def admin_assign_room(request, application_id):
    """
    Назначение комнаты заявке.
    """
    app = get_object_or_404(Application, id=application_id)
    room_id = request.POST.get('room_id')
    
    if room_id:
        room = get_object_or_404(Room, id=room_id)
        
        # Проверяем, есть ли места
        if room.available_beds() > 0:
            app.assigned_room = room
            app.status = 'assigned'
            app.save()
            
            # Увеличиваем счётчик заселённых
            room.current_occupancy += 1
            room.save()
            
            messages.success(request, f'Комната {room.number} назначена студенту {app.student.get_full_name()}.')
        else:
            messages.error(request, 'В этой комнате нет свободных мест.')
    else:
        messages.error(request, 'Комната не выбрана.')
    
    return redirect('applications:admin_application_detail', application_id=application_id)


@staff_member_required
def admin_rating_list(request):
    """
    Рейтинговый список всех заявок.
    """
    applications = Application.objects.filter(
        status__in=['submitted', 'under_review', 'approved']
    ).select_related('student').order_by('-rating_score', 'created_at')
    
    return render(request, 'applications/admin_rating_list.html', {
        'applications': applications,
    })


# ============================================================================
# ПРЕДСТАВЛЕНИЯ ДЛЯ КОМЕНДАНТА
# ============================================================================

@login_required
def commandant_dashboard(request):
    """
    Панель управления коменданта.
    Показывает общежитие, за которое отвечает комендант.
    """
    if request.user.role != 'commandant':
        messages.error(request, 'Доступ запрещён.')
        return redirect('applications:status')
    
    dormitory = request.user.dormitory
    if not dormitory:
        messages.error(request, 'Вам не назначено общежитие. Обратитесь к техническому администратору.')
        return redirect('applications:status')
    
    # Получаем комнаты этого общежития
    rooms = Room.objects.filter(dormitory=dormitory).select_related('dormitory')
    
    # Получаем заявки, назначенные в это общежитие
    applications = Application.objects.filter(
        assigned_room__dormitory=dormitory,
        status='assigned'
    ).select_related('student', 'assigned_room')
    
    # Статистика
    total_rooms = rooms.count()
    occupied_rooms = rooms.filter(status='occupied').count()
    available_rooms = rooms.filter(status='available').count()
    repair_rooms = rooms.filter(status='under_repair').count()
    
    occupancy_rate = int((occupied_rooms / total_rooms * 100)) if total_rooms > 0 else 0
    
    return render(request, 'applications/commandant_dashboard.html', {
        'dormitory': dormitory,
        'rooms': rooms,
        'applications': applications,
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'available_rooms': available_rooms,
        'repair_rooms': repair_rooms,
        'occupancy_rate': occupancy_rate,
    })


@login_required
def commandant_check_in(request, application_id):
    """
    Отметка о фактическом заселении студента.
    """
    if request.user.role != 'commandant':
        messages.error(request, 'Доступ запрещён.')
        return redirect('applications:status')
    
    app = get_object_or_404(Application, id=application_id)
    
    # Проверяем, что комендант отвечает за это общежитие
    if app.assigned_room and app.assigned_room.dormitory != request.user.dormitory:
        messages.error(request, 'Вы не отвечаете за это общежитие.')
        return redirect('applications:commandant_dashboard')
    
    if app.status == 'assigned':
        app.status = 'checked_in'
        app.save()
        messages.success(request, f'Студент {app.student.get_full_name()} заселён.')
    else:
        messages.warning(request, 'Невозможно заселить студента в текущем статусе.')
    
    return redirect('applications:commandant_dashboard')


@login_required
def commandant_check_out(request, application_id):
    """
    Отметка о выселении студента.
    """
    if request.user.role != 'commandant':
        messages.error(request, 'Доступ запрещён.')
        return redirect('applications:status')
    
    app = get_object_or_404(Application, id=application_id)
    
    if app.assigned_room and app.assigned_room.dormitory != request.user.dormitory:
        messages.error(request, 'Вы не отвечаете за это общежитие.')
        return redirect('applications:commandant_dashboard')
    
    if app.status == 'checked_in':
        app.status = 'checked_out'
        
        # Уменьшаем счётчик заселённых
        if app.assigned_room:
            app.assigned_room.current_occupancy = max(0, app.assigned_room.current_occupancy - 1)
            app.assigned_room.save()
        
        app.save()
        messages.success(request, f'Студент {app.student.get_full_name()} выселен.')
    else:
        messages.warning(request, 'Невозможно выселить студента в текущем статусе.')
    
    return redirect('applications:commandant_dashboard')


# ============================================================================
# AJAX ПРЕДСТАВЛЕНИЯ
# ============================================================================

@login_required
def get_available_rooms(request):
    """
    AJAX: Получение списка свободных комнат.
    """
    dormitory_id = request.GET.get('dormitory_id')
    
    if dormitory_id:
        rooms = Room.objects.filter(
            dormitory_id=dormitory_id,
            status='available'
        ).annotate(
            available_beds=F('capacity') - F('current_occupancy')
        ).filter(
            available_beds__gt=0
        ).values('id', 'number', 'floor', 'capacity', 'available_beds')
        
        return JsonResponse({'rooms': list(rooms)})
    
    return JsonResponse({'rooms': []})


@login_required
def calculate_rating_preview(request):
    """
    AJAX: Предварительный расчёт рейтинга.
    """
    if request.method == 'GET':
        ege_score = float(request.GET.get('ege_score', 0))
        diploma_type = request.GET.get('diploma_type', 'regular')
        distance_km = int(request.GET.get('distance_km', 0))
        has_priority = request.GET.get('has_priority_benefit') == 'true'
        is_orphan = request.GET.get('is_orphan') == 'true'
        is_disabled = request.GET.get('is_disabled') == 'true'
        
        # Создаём временный объект для расчёта
        temp_app = Application(
            ege_score=ege_score,
            diploma_type=diploma_type,
            distance_km=distance_km,
            has_priority_benefit=has_priority,
            is_orphan=is_orphan,
            is_disabled=is_disabled,
        )
        
        score = calculate_rating(temp_app)
        
        return JsonResponse({'rating_score': score})
    
    return JsonResponse({'error': 'Invalid method'}, status=400)

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q, F
import json
from django.http import JsonResponse

@login_required
@staff_member_required
def admin_analytics(request):
    """
    Панель аналитики для технического администратора.
    Собирает данные о заявках, заполненности и динамике.
    """
    # 1. Общая статистика
    total_apps = Application.objects.count()
    approved_apps = Application.objects.filter(status='approved').count()
    assigned_apps = Application.objects.filter(status='assigned').count()
    housed_apps = Application.objects.filter(status='checked_in').count()

    # 2. Статистика по статусам (для круговой диаграммы)
    status_stats = Application.objects.values('status').annotate(count=Count('id')).order_by('status')
    # Преобразуем в понятный для JS формат
    labels = []
    data_counts = []
    status_names = dict(Application.STATUS_CHOICES)
    
    for item in status_stats:
        labels.append(status_names.get(item['status'], item['status']))
        data_counts.append(item['count'])

    # 3. Заполненность общежитий (для столбчатой диаграммы)
    # Мы считаем реальные заселения через связанные заявки
    from dorms.models import Dormitory
    dorms_stats = Dormitory.objects.annotate(
        total_beds=Sum('rooms__capacity'),
        occupied_beds=Count(
            'rooms__assigned_applications', 
            filter=Q(rooms__assigned_applications__status='checked_in'), 
            distinct=True
        )
    )

    dorm_labels = [d.name for d in dorms_stats]
    dorm_capacity = [d.total_beds or 0 for d in dorms_stats]
    dorm_occupied = [d.occupied_beds or 0 for d in dorms_stats]

    context = {
        'stats': {
            'total': total_apps,
            'approved': approved_apps,
            'assigned': assigned_apps,
            'housed': housed_apps
        },
        'chart_data': json.dumps({
            'status_labels': labels,
            'status_counts': data_counts,
            'dorm_labels': dorm_labels,
            'dorm_capacity': dorm_capacity,
            'dorm_occupied': dorm_occupied
        })
    }
    
    return render(request, 'applications/admin_analytics.html', context)