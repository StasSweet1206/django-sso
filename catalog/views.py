from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import Category, Product
import json

# Декоратор для добавления CORS заголовков
def add_cors_headers(view_func):
    def wrapped_view(request, *args, **kwargs):
        # Обработка preflight запроса
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response

        # Обычный запрос
        response = view_func(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    return wrapped_view

@csrf_exempt
@add_cors_headers
def category_list(request):
    """Получить список всех категорий с пагинацией"""
    try:
        # Получаем параметры пагинации
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))

        # Получаем все категории
        categories = Category.objects.all().order_by('name')

        # Пагинация
        paginator = Paginator(categories, page_size)
        page_obj = paginator.get_page(page)

        # Формируем ответ
        data = {
            'count': paginator.count,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': [
                {
                    'id': cat.id,
                    'guid': str(cat.guid),
                    'name': cat.name,
                    'parent_id': cat.parent.id if cat.parent else None,
                    'image': cat.image.url if cat.image else None,
                    'created_at': cat.created_at.isoformat(),
                    'updated_at': cat.updated_at.isoformat(),
                }
                for cat in page_obj
            ]
        }

        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@add_cors_headers
def category_detail(request, category_id):
    """Получить детальную информацию о категории"""
    try:
        category = Category.objects.get(id=category_id)

        data = {
            'id': category.id,
            'guid': str(category.guid),
            'name': category.name,
            'parent_id': category.parent.id if category.parent else None,
            'image': category.image.url if category.image else None,
            'created_at': category.created_at.isoformat(),
            'updated_at': category.updated_at.isoformat(),
        }

        return JsonResponse(data)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Категория не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@add_cors_headers
def product_list(request):
    """Получить список товаров с фильтрацией и пагинацией"""
    try:
        # Получаем параметры
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        category_id = request.GET.get('category')
        search = request.GET.get('search', '')

        # Базовый queryset
        products = Product.objects.all()

        # Фильтрация по категории
        if category_id:
            products = products.filter(category_id=category_id)

        # Поиск по названию
        if search:
            products = products.filter(name__icontains=search)

        # Сортировка
        products = products.order_by('name')

        # Пагинация
        paginator = Paginator(products, page_size)
        page_obj = paginator.get_page(page)

        # Формируем ответ
        data = {
            'count': paginator.count,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': [
                {
                    'id': prod.id,
                    'guid': str(prod.guid),
                    'name': prod.name,
                    'article': prod.article,
                    'price': float(prod.price),
                    'category_id': prod.category.id if prod.category else None,
                    'category_name': prod.category.name if prod.category else None,
                    'image': prod.image.url if prod.image else None,
                    'in_stock': prod.in_stock,
                    'created_at': prod.created_at.isoformat(),
                    'updated_at': prod.updated_at.isoformat(),
                }
                for prod in page_obj
            ]
        }

        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@add_cors_headers
def product_detail(request, product_id):
    """Получить детальную информацию о товаре"""
    try:
        product = Product.objects.get(id=product_id)

        data = {
            'id': product.id,
            'guid': str(product.guid),
            'name': product.name,
            'article': product.article,
            'price': float(product.price),
            'description': product.description,
            'category_id': product.category.id if product.category else None,
            'category_name': product.category.name if product.category else None,
            'image': product.image.url if product.image else None,
            'in_stock': product.in_stock,
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat(),
        }

        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Товар не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)