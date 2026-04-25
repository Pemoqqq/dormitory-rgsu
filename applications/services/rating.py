from applications.models import Application

def calculate_rating(app_instance):
    """
    Расчёт рейтингового балла на основе критериев из п. 1.2 диплома РГСУ.
    """
    score = 0.0

    # 1. Приоритетные категории (ФЗ №273, ст. 36) - максимальный вес
    # Дети-сироты, дети-инвалиды, инвалиды I и II групп
    if app_instance.is_orphan or app_instance.is_disabled:
        score += 1000
        print(f"Начислено 1000 баллов (Льготная категория) для {app_instance.student}")
    elif app_instance.has_priority_benefit:
        score += 500
        print(f"Начислено 500 баллов (Иная льгота) для {app_instance.student}")

    # 2. Баллы ЕГЭ
    # Если есть баллы, добавляем их
    if app_instance.ege_score:
        score += float(app_instance.ege_score)

    # 3. Тип аттестата/диплома
    # "студенты с красными аттестатами или дипломами"
    if app_instance.diploma_type == 'red_high_school': # Аттестат с отличием
        score += 50
    elif app_instance.diploma_type == 'red_college': # Диплом СПО с отличием
        score += 40

    # 4. Территориальный коэффициент
    # "учитывается удалённость места жительства" (пример: > 500 км)
    if app_instance.distance_km:
        dist = int(app_instance.distance_km)
        if dist > 1000:
            score += 50
        elif dist > 500:
            score += 30
            
    # Сохраняем итоговый балл в экземпляр
    app_instance.rating_score = score
    return score

def update_queue_positions():
    """
    Присваивает позиции в очереди всем активным заявкам на основе рейтинга.
    """
    # Берём только заявки, которые находятся в процессе
    active_statuses = ['submitted', 'under_review', 'approved']
    
    # Сортируем: сначала самый высокий рейтинг, потом те, кто раньше подал (created_at)
    applications = Application.objects.filter(status__in=active_statuses).order_by(
        '-rating_score', 
        'created_at'
    )

    position = 1
    for app in applications:
        app.queue_position = position
        app.save(update_fields=['queue_position'])
        position += 1

    print(f"Обновлены позиции очереди для {position - 1} заявок.")