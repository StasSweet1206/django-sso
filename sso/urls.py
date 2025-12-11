from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check), 
    path('admin/', admin.site.urls),
    path('health/', views.health_check),
]