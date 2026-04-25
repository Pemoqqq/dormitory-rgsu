from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Студент / Абитуриент
    path('create/', views.create_application, name='create'),
    path('upload/', views.upload_documents, name='upload'),
    path('status/', views.application_status, name='status'),
    path('cancel/<int:application_id>/', views.cancel_application, name='cancel'),

    # Администратор приёмной комиссии
    path('admin/list/', views.admin_application_list, name='admin_application_list'),
    path('admin/detail/<int:application_id>/', views.admin_application_detail, name='admin_application_detail'),
    path('admin/verify-doc/<int:document_id>/', views.admin_verify_document, name='admin_verify_document'),
    path('admin/update-status/<int:application_id>/', views.admin_update_application_status, name='admin_update_application_status'),
    path('admin/assign-room/<int:application_id>/', views.admin_assign_room, name='admin_assign_room'),
    path('admin/rating/', views.admin_rating_list, name='admin_rating_list'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    
    # Комендант общежития
    path('commandant/dashboard/', views.commandant_dashboard, name='commandant_dashboard'),
    path('commandant/check-in/<int:application_id>/', views.commandant_check_in, name='commandant_check_in'),
    path('commandant/check-out/<int:application_id>/', views.commandant_check_out, name='commandant_check_out'),

    # AJAX (динамические данные без перезагрузки)
    path('ajax/rooms/', views.get_available_rooms, name='get_available_rooms'),
    path('ajax/rating-preview/', views.calculate_rating_preview, name='calculate_rating_preview'),
]