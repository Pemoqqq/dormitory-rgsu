import uuid
import os
from django.db import models
from django.conf import settings
from django.utils import timezone


def application_doc_path(instance, filename):
    """
    Генерирует уникальный путь для загрузки документов.
    Формат: docs/{username}/{doc_type}_{timestamp}.{ext}
    """
    ext = filename.split('.')[-1]
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    return f'docs/{instance.application.student.username}/{instance.doc_type}_{timestamp}_{unique_id}.{ext}'


class Application(models.Model):
    """
    Заявка студента на заселение в общежитие.
    Соответствует п. 1.1 диплома: автоматизация подачи и рассмотрения заявлений.
    """
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('submitted', 'Отправлена на рассмотрение'),
        ('under_review', 'На проверке'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
        ('assigned', 'Место назначено'),
        ('checked_in', 'Заселён'),
        ('checked_out', 'Выселен'),
    ]

    DIPLOMA_TYPE_CHOICES = [
        ('regular', 'Обычный аттестат/диплом'),
        ('red_high_school', 'Аттестат с отличием (школа)'),
        ('red_college', 'Диплом с отличием (СПО)'),
    ]

    # Связь с пользователем (студентом)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Студент/Абитуриент'
    )
    
    # Даты создания и обновления
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подачи заявки'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата последнего изменения'
    )
    
    # Статус заявки
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус заявки'
    )
    
    # Данные для расчёта рейтинга (п. 1.2 диплома)
    ege_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Сумма баллов ЕГЭ'
    )
    
    diploma_type = models.CharField(
        max_length=20,
        choices=DIPLOMA_TYPE_CHOICES,
        default='regular',
        verbose_name='Тип аттестата/диплома'
    )
    
    distance_km = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Расстояние от места жительства (км)'
    )
    
    # Льготные категории (ч. 5 ст. 36 ФЗ №273)
    has_priority_benefit = models.BooleanField(
        default=False,
        verbose_name='Льготная категория (сироты, инвалиды и др.)'
    )
    
    is_orphan = models.BooleanField(
        default=False,
        verbose_name='Ребёнок-сирота'
    )
    
    is_disabled = models.BooleanField(
        default=False,
        verbose_name='Инвалид I или II группы'
    )
    
    # Итоговый рейтинг и позиция в очереди
    rating_score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.0,
        verbose_name='Рейтинговый балл'
    )
    
    queue_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Место в очереди'
    )
    
    # Назначенная комната (заполняется администратором)
    assigned_room = models.ForeignKey(
        'dorms.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_applications',
        verbose_name='Назначенная комната'
    )
    
    # Дополнительные комментарии
    admin_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий администратора'
    )

    class Meta:
        verbose_name = 'Заявка на заселение'
        verbose_name_plural = 'Заявки на заселение'
        ordering = ['-rating_score', 'created_at']
        unique_together = ['student', 'created_at']  # Один студент — одна заявка на период

    def __str__(self):
        return f"Заявка #{self.id} | {self.student.get_full_name()} | {self.get_status_display()}"

    def calculate_rating(self):
        """
        Алгоритм расчёта рейтингового балла.
        Соответствует п. 1.2 диплома: приоритеты распределения.
        """
        score = 0.0
        
        # 1. Приоритетные категории (ФЗ №273) — максимальный приоритет
        if self.is_orphan or self.is_disabled:
            score += 1000
        
        if self.has_priority_benefit:
            score += 500
        
        # 2. Баллы ЕГЭ
        if self.ege_score:
            score += float(self.ege_score)
        
        # 3. Аттестат/диплом с отличием
        if self.diploma_type == 'red_high_school':
            score += 50
        elif self.diploma_type == 'red_college':
            score += 40
        
        # 4. Территориальный коэффициент (удалённость > 500 км)
        if self.distance_km and self.distance_km > 500:
            score += 30
        elif self.distance_km and self.distance_km > 1000:
            score += 50
        
        self.rating_score = score
        return score


class Document(models.Model):
    """
    Загруженные скан-копии документов.
    Соответствует п. 1.2: требования к документам для заселения.
    """
    DOC_TYPE_CHOICES = [
        ('passport_main', 'Паспорт (разворот с фото)'),
        ('passport_registration', 'Паспорт (прописка)'),
        ('medical_086', 'Медицинская справка 086/у'),
        ('fluoro', 'Флюорография'),
        ('vaccination', 'Прививочный сертификат'),
        ('hiv_certificate', 'Справка об отсутствии ВИЧ (для иностранцев)'),
        ('benefit_proof', 'Подтверждение льготы'),
        ('achievement', 'Достижения (олимпиады, грамоты)'),
        ('parent_passport', 'Паспорт законного представителя'),
        ('parent_consent', 'Согласие законного представителя'),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Заявка'
    )
    
    doc_type = models.CharField(
        max_length=30,
        choices=DOC_TYPE_CHOICES,
        verbose_name='Тип документа'
    )
    
    file = models.FileField(
        upload_to=application_doc_path,
        verbose_name='Файл документа'
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Проверен администратором'
    )
    
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents',
        verbose_name='Проверил'
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата проверки'
    )
    
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий к проверке'
    )

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        unique_together = ['application', 'doc_type']  # Один тип документа на заявку
        ordering = ['doc_type', 'uploaded_at']

    def __str__(self):
        return f"{self.get_doc_type_display()} для {self.application.student.get_full_name()}"


class Contract(models.Model):
    """
    Договор найма жилого помещения.
    Соответствует п. 1.2: этап заключения договора.
    """
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='contract',
        verbose_name='Заявка'
    )
    
    contract_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Номер договора'
    )
    
    start_date = models.DateField(
        verbose_name='Дата начала действия'
    )
    
    end_date = models.DateField(
        verbose_name='Дата окончания действия'
    )
    
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name='Ежемесячная плата (руб.)'
    )
    
    # Файл договора (генерируется автоматически или загружается)
    file = models.FileField(
        upload_to='contracts/',
        null=True,
        blank=True,
        verbose_name='PDF-копия договора'
    )
    
    # Статус подписания
    is_signed_by_student = models.BooleanField(
        default=False,
        verbose_name='Подписан студентом'
    )
    
    is_signed_by_university = models.BooleanField(
        default=False,
        verbose_name='Подписан университетом'
    )
    
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата подписания'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Договор найма'
        verbose_name_plural = 'Договоры найма'
        ordering = ['-created_at']

    def __str__(self):
        return f"Договор №{self.contract_number} | {self.application.student.get_full_name()}"