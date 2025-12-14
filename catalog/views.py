from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Category, Product

def add_cors_headers(response):
    """Добавить CORS заголовки к ответу"""
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def category_list(request):
    """Получить список категорий с пагинацией"""
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)

    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))

        categories = Category.objects.all()
        total = categories.count()

        start = (page - 1) * page_size
        end = start + page_size

        categories_page = categories[start:end]

        response = JsonResponse({
            'count': total,
            'next': page + 1 if end < total else None,
            'previous': page - 1 if page > 1 else None,
            'results': [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'guid': str(cat.guid),
                }
                for cat in categories_page
            ]
        })

        return add_cors_headers(response)

    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def category_detail(request, category_id):
    """Получить детали категории"""
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)

    try:
        category = Category.objects.get(id=category_id)
        response = JsonResponse({
            'id': category.id,
            'name': category.name,
            'guid': str(category.guid),
        })
        return add_cors_headers(response)

    except Category.DoesNotExist:
        response = JsonResponse({'error': 'Category not found'}, status=404)
        return add_cors_headers(response)
    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def product_list(request):
    """Получить список товаров"""
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)

    try:
        products = Product.objects.all()[:20]
        response = JsonResponse({
            'count': products.count(),
            'results': [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': float(p.price),
                }
                for p in products
            ]
        })
        return add_cors_headers(response)

    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def product_detail(request, product_id):
    """Получить детали товара"""
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)

    try:
        product = Product.objects.get(id=product_id)
        response = JsonResponse({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
        })
        return add_cors_headers(response)

    except Product.DoesNotExist:
        response = JsonResponse({'error': 'Product not found'}, status=404)
        return add_cors_headers(response)
    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        return add_cors_headers(response)