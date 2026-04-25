from django.contrib import admin
from .models import Application, Document, Contract

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_name', 'status', 'rating_score', 'queue_position', 'created_at')
    list_filter = ('status', 'diploma_type', 'has_priority_benefit', 'is_orphan', 'is_disabled')
    search_fields = ('student__last_name', 'student__first_name', 'student__patronymic', 'student__username')
    readonly_fields = ('rating_score', 'queue_position', 'created_at', 'updated_at')
    ordering = ('-rating_score', 'created_at')
    
    fieldsets = (
        ('Основные данные', {'fields': ('student', 'status', 'created_at', 'updated_at')}),
        ('Академические и социальные параметры', {'fields': ('ege_score', 'diploma_type', 'distance_km', 'has_priority_benefit', 'is_orphan', 'is_disabled')}),
        ('Распределение', {'fields': ('rating_score', 'queue_position', 'assigned_room', 'admin_comment')}),
    )

    def student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username
    student_name.short_description = 'Студент'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_type', 'application', 'uploaded_at', 'is_verified', 'verified_by')
    list_filter = ('doc_type', 'is_verified')
    search_fields = ('application__student__last_name', 'application__student__first_name')
    readonly_fields = ('uploaded_at', 'verified_at', 'verified_by')
    
    def save_model(self, request, obj, form, change):
        if obj.is_verified and not obj.verified_by:
            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'application', 'start_date', 'end_date', 'is_signed_by_student', 'is_signed_by_university')
    list_filter = ('is_signed_by_student', 'is_signed_by_university')
    search_fields = ('contract_number', 'application__student__last_name', 'application__student__first_name')
    readonly_fields = ('created_at', 'signed_at')
    
    fieldsets = (
        ('Реквизиты', {'fields': ('contract_number', 'application', 'start_date', 'end_date', 'monthly_fee')}),
        ('Документ', {'fields': ('file',)}),
        ('Подписание', {'fields': ('is_signed_by_student', 'is_signed_by_university', 'signed_at')}),
    )