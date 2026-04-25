from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Настройка административной панели для кастомной модели User.
    Добавляет отображение ролей, факультета и закреплённого общежития.
    """
    
    # Поля, отображаемые в списке пользователей
    list_display = ('username', 'email', 'get_full_name', 'role', 'faculty', 'is_active', 'is_staff')
    
    # Фильтры в правой панели
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'faculty')
    
    # Поля для поиска
    search_fields = ('username', 'first_name', 'last_name', 'email', 'patronymic')
    
    # Поля, доступные для редактирования в списке (быстрое редактирование)
    list_editable = ('role', 'is_active')
    
    # Группировка полей на странице редактирования
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'patronymic', 'email')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
        ('Дополнительная информация', {'fields': ('role', 'phone', 'faculty', 'dormitory')}),
    )
    
    # Поля при создании нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
        ('Персональная информация', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'patronymic', 'phone', 'faculty'),
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    # Порядок отображения полей
    ordering = ('-date_joined',)
    
    # Только для чтения (нельзя изменить)
    readonly_fields = ('last_login', 'date_joined')
    
    def get_full_name(self, obj):
        """Возвращает полное ФИО пользователя."""
        full_name = f"{obj.last_name} {obj.first_name} {obj.patronymic or ''}".strip()
        return full_name if full_name else obj.username
    
    get_full_name.short_description = 'ФИО'
    get_full_name.admin_order_field = 'last_name'