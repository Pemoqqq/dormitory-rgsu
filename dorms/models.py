from django.db import models

class Dormitory(models.Model):
    """
    Модель общежития (корпуса).
    Соответствует п. 1.1 диплома: управление жилым фондом РГСУ.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='Название корпуса'
    )
    address = models.CharField(
        max_length=255,
        verbose_name='Адрес'
    )
    total_capacity = models.PositiveIntegerField(
        verbose_name='Общая вместимость (чел.)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    class Meta:
        verbose_name = 'Общежитие'
        verbose_name_plural = 'Общежития'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.address})"


class Room(models.Model):
    """
    Модель комнаты в общежитии.
    Позволяет коменданту управлять фондом комнат (п. 1.1 диплома).
    """
    STATUS_CHOICES = [
        ('available', 'Свободна'),
        ('occupied', 'Занята'),
        ('under_repair', 'На ремонте'),
        ('reserved', 'Зарезервирована'),
    ]

    dormitory = models.ForeignKey(
        Dormitory,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name='Общежитие'
    )
    number = models.CharField(
        max_length=10,
        verbose_name='Номер комнаты'
    )
    floor = models.PositiveIntegerField(
        verbose_name='Этаж'
    )
    capacity = models.PositiveIntegerField(
        default=2,
        verbose_name='Вместимость (чел.)'
    )
    current_occupancy = models.PositiveIntegerField(
        default=0,
        verbose_name='Заселено'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name='Статус'
    )

    class Meta:
        verbose_name = 'Комната'
        verbose_name_plural = 'Комнаты'
        unique_together = ('dormitory', 'number')  # Уникальность номера в рамках корпуса
        ordering = ['dormitory', 'floor', 'number']

    def __str__(self):
        return f"{self.dormitory.name} - комн. {self.number} (эт. {self.floor})"

    def is_full(self):
        """Проверка, заполнена ли комната."""
        return self.current_occupancy >= self.capacity

    def available_beds(self):
        """Количество свободных мест."""
        return max(0, self.capacity - self.current_occupancy)