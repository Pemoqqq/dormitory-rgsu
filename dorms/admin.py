from django.contrib import admin
from .models import Dormitory, Room

@admin.register(Dormitory)
class DormitoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'total_capacity', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'dormitory', 'floor', 'capacity', 'current_occupancy', 'status')
    list_filter = ('dormitory', 'floor', 'status')
    search_fields = ('number',)
    readonly_fields = ('current_occupancy',)  # Заполняется автоматически при заселении