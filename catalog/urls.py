from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('categories/', views.categories_list, name='categories-list'),
    path('categories/tree/', views.category_tree, name='categories-tree'),
    path('products/', views.products_list, name='products-list'),
    path('products/<int:product_id>/', views.product_detail, name='product-detail'),
]