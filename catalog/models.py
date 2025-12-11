"""
Модели каталога товаров
"""
from django.db import models


class Category(models.Model):
    """Категория товаров из 1С"""

    code_1c = models.CharField(
        'Код 1С',
        max_length=255,
        unique=True,
        db_index=True
    )

    name = models.CharField(
        'Название',
        max_length=255
    )

    description = models.TextField(
        'Описание',
        blank=True,
        default=''
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='Родительская категория',
        null=True,
        blank=True,
        db_column='parent_id'  # Имя колонки в БД будет parent_id
    )

    parent_code_1c = models.CharField(
        'Код 1С родительской категории',
        max_length=255,
        blank=True,
        default='',
        help_text='00000000-0000-0000-0000-000000000000 = корневая категория'
    )

    is_active = models.BooleanField(
        'Активна',
        default=True
    )

    order = models.IntegerField(
        'Порядок сортировки',
        default=0,
        db_index=True
    )

    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['code_1c']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар (номенклатура)"""
    code_1c = models.CharField('Код 1С', max_length=100, unique=True, db_index=True)
    name = models.CharField('Название', max_length=255)
    full_name = models.TextField('Полное название', blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Категория'
    )
    image_url = models.URLField('Ссылка на изображение', blank=True)
    has_variants = models.BooleanField('Есть характеристики', default=False)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        db_table = 'catalog_product'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """Вариант товара (характеристика)"""
    code_1c = models.CharField('Код 1С', max_length=100, unique=True, db_index=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name='Товар'
    )
    name = models.CharField('Название характеристики', max_length=255)
    full_name = models.TextField('Полное название', blank=True)
    image_url = models.URLField('Ссылка на изображение', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        db_table = 'catalog_product_variant'
        verbose_name = 'Вариант товара'
        verbose_name_plural = 'Варианты товаров'
        ordering = ['name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"