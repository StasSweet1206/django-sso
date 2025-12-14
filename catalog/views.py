from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from .models import Category, Product, ProductVariant


@csrf_exempt
@require_http_methods(["GET"])
def categories_list(request):
    """Получение списка категорий"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        parent_code = request.GET.get('parent')  # Фильтр по родительской категории

        # Получаем только активные категории
        categories = Category.objects.filter(is_active=True)

        # Если запрашивают корневые категории
        if parent_code == 'root' or not parent_code:
            categories = categories.filter(
                Q(parent__isnull=True) | 
                Q(parent_code_1c='00000000-0000-0000-0000-000000000000')
            )
        elif parent_code:
            categories = categories.filter(parent_code_1c=parent_code)

        # Пагинация
        paginator = Paginator(categories, page_size)
        page_obj = paginator.get_page(page)

        results = [
            {
                "id": cat.id,
                "code_1c": cat.code_1c,
                "name": cat.name,
                "description": cat.description,
                "parent_code_1c": cat.parent_code_1c,
                "has_children": cat.children.filter(is_active=True).exists(),
                "products_count": cat.products.filter(is_active=True).count(),
                "order": cat.order
            }
            for cat in page_obj
        ]

        return JsonResponse({
            "results": results,
            "count": paginator.count,
            "next": page_obj.next_page_number() if page_obj.has_next() else None,
            "previous": page_obj.previous_page_number() if page_obj.has_previous() else None
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def products_list(request):
    """Получение списка товаров"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        category_code = request.GET.get('category')
        search = request.GET.get('search', '').strip()

        # Получаем активные товары с категориями
        products = Product.objects.filter(is_active=True).select_related('category')

        # Фильтр по категории
        if category_code:
            products = products.filter(category__code_1c=category_code)

        # Поиск
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(full_name__icontains=search) |
                Q(code_1c__icontains=search)
            )

        # Пагинация
        paginator = Paginator(products, page_size)
        page_obj = paginator.get_page(page)

        results = []
        for prod in page_obj:
            product_data = {
                "id": prod.id,
                "code_1c": prod.code_1c,
                "name": prod.name,
                "full_name": prod.full_name,
                "image": prod.image_url or "",
                "has_variants": prod.has_variants,
                "category": None
            }

            if prod.category:
                product_data["category"] = {
                    "id": prod.category.id,
                    "code_1c": prod.category.code_1c,
                    "name": prod.category.name
                }

            results.append(product_data)

        return JsonResponse({
            "results": results,
            "count": paginator.count,
            "next": page_obj.next_page_number() if page_obj.has_next() else None,
            "previous": page_obj.previous_page_number() if page_obj.has_previous() else None
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def product_detail(request, product_id):
    """Получение детальной информации о товаре"""
    try:
        product = Product.objects.select_related('category').prefetch_related(
            Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True))
        ).get(id=product_id, is_active=True)

        # Варианты товара
        variants = [
            {
                "id": var.id,
                "code_1c": var.code_1c,
                "name": var.name,
                "full_name": var.full_name,
                "image": var.image_url or ""
            }
            for var in product.variants.all()
        ]

        response_data = {
            "id": product.id,
            "code_1c": product.code_1c,
            "name": product.name,
            "full_name": product.full_name,
            "image": product.image_url or "",
            "has_variants": product.has_variants,
            "variants": variants,
            "category": None,
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat()
        }

        if product.category:
            response_data["category"] = {
                "id": product.category.id,
                "code_1c": product.category.code_1c,
                "name": product.category.name
            }

        return JsonResponse(response_data)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def category_tree(request):
    """Получение дерева категорий"""
    try:
        def build_tree(parent_code='00000000-0000-0000-0000-000000000000'):
            categories = Category.objects.filter(
                is_active=True,
                parent_code_1c=parent_code
            ).order_by('order', 'name')

            result = []
            for cat in categories:
                cat_data = {
                    "id": cat.id,
                    "code_1c": cat.code_1c,
                    "name": cat.name,
                    "description": cat.description,
                    "order": cat.order,
                    "products_count": cat.products.filter(is_active=True).count(),
                    "children": build_tree(cat.code_1c)
                }
                result.append(cat_data)

            return result

        tree = build_tree()

        return JsonResponse({"categories": tree})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)