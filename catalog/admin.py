"""
Административная панель каталога
"""
from django.contrib import admin
from .models import Category, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Администрирование категорий"""

    list_display = ['name','code_1c','parent','order','is_active','created_at']

    list_filter = [ 'is_active','created_at']

    search_fields = ['name','code_1c','description']

    readonly_fields = ['code_1c','created_at','updated_at']

    fieldsets = (
        ('Основная информация', {'fields': ('code_1c','name','description','parent','order')}),
        ('Статус', {'fields': ('is_active',)}),
        ('Системная информация', {'fields': ('created_at','updated_at'),'classes': ('collapse',)}),
    )

    ordering = ['order', 'name']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['name', 'full_name', 'code_1c', 'image_url', 'is_active']
    readonly_fields = ['code_1c']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'code_1c', 'category', 'has_variants', 'is_active']
    list_filter = ['is_active', 'has_variants', 'category']
    search_fields = ['name', 'code_1c', 'full_name']
    list_editable = ['is_active']
    inlines = [ProductVariantInline]
    readonly_fields = ['code_1c', 'created_at', 'updated_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('code_1c', 'name', 'full_name', 'category')
        }),
        ('Изображения', {
            'fields': ('image_url',)
        }),
        ('Настройки', {
            'fields': ('has_variants', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'code_1c', 'is_active']
    list_filter = ['is_active', 'product']
    search_fields = ['name', 'code_1c', 'full_name']
    list_editable = ['is_active']
    readonly_fields = ['code_1c', 'created_at', 'updated_at']