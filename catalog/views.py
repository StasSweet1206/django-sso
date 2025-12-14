from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Category, Product

@csrf_exempt
def category_list(request):
    """Получить список всех категорий"""
    try:
        # Добавляем CORS сразу
        response_data = {
            'status': 'ok',
            'count': 0,
            'results': []
        }

        # Пробуем получить категории
        categories = Category.objects.all()[:20]

        response_data['count'] = categories.count()
        response_data['results'] = [
            {
                'id': cat.id,
                'name': cat.name,
                'guid': str(cat.guid),
            }
            for cat in categories
        ]

        response = JsonResponse(response_data)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = '*'

        return response

    except Exception as e:
        # Логируем ошибку
        import traceback
        print("ERROR in category_list:", str(e))
        print(traceback.format_exc())

        response = JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response

@csrf_exempt
def category_detail(request, category_id):
    """Детали категории"""
    try:
        category = Category.objects.get(id=category_id)

        response = JsonResponse({
            'id': category.id,
            'name': category.name,
            'guid': str(category.guid),
        })
        response['Access-Control-Allow-Origin'] = '*'
        return response

    except Category.DoesNotExist:
        response = JsonResponse({'error': 'Not found'}, status=404)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response

@csrf_exempt
def product_list(request):
    """Список товаров"""
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
        response['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response

@csrf_exempt
def product_detail(request, product_id):
    """Детали товара"""
    try:
        product = Product.objects.get(id=product_id)

        response = JsonResponse({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
        })
        response['Access-Control-Allow-Origin'] = '*'
        return response

    except Product.DoesNotExist:
        response = JsonResponse({'error': 'Not found'}, status=404)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response