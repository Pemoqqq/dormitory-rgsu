from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Кастомная модель пользователя для информационной системы заселения РГСУ.
    Расширяет стандартную модель Django, добавляя роли, контактные данные 
    и привязку к общежитию (для комендантов).
    """
    ROLE_CHOICES = [
        ('student', 'Студент/Абитуриент'),
        ('admin', 'Администратор'),
        ('commandant', 'Комендант'),
        ('tech_admin', 'Технический администратор'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name='Роль пользователя'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    
    faculty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Факультет'
    )
    
    patronymic = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отчество'
    )

    # Связь с общежитием. Используется строковая ссылка для избежания 
    # циклических импортов между приложениями users и dorms.
    dormitory = models.ForeignKey(
        'dorms.Dormitory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Закреплённое общежитие'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        """Возвращает ФИО или username, если ФИО не заполнено."""
        full_name = f"{self.last_name} {self.first_name} {self.patronymic}".strip()
        return full_name if full_name else self.username