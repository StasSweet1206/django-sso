from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.health_check), 
    path('admin/', admin.site.urls),
    path('health/', views.health_check),
    path('api/catalog/', include('catalog.urls')),
]