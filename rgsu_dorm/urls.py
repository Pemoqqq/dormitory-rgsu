"""
URL configuration for rgsu_dorm project.
Маршрутизация запросов для информационной системы заселения в общежития РГСУ.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Панель администратора Django
    path('admin/', admin.site.urls),

    # Аутентификация: вход и выход
    path('accounts/login/', auth_views.LoginView.as_view(template_name='applications/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Личный кабинет студента (основной функционал системы)
    path('cab/', include('applications.urls', namespace='applications')),
    
    # При необходимости можно добавить маршруты для панели коменданта/администратора:
    # path('staff/', include('staff.urls', namespace='staff')),
]

# Раздача медиа- и статических файлов только в режиме отладки (DEBUG = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)