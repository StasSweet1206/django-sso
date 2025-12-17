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
        parent_id = request.GET.get('parent')  # ✅ ИЗМЕНЕНО: parent_id вместо parent_code

        # Получаем только активные категории
        categories = Category.objects.filter(is_active=True)

        # ✅ ИЗМЕНЕНО: Фильтруем по parent_id
        if parent_id == 'root' or not parent_id:
            # Корневые категории (без родителя)
            categories = categories.filter(parent__isnull=True)
        else:
            # Подкатегории с конкретным родителем
            try:
                parent_id = int(parent_id)
                categories = categories.filter(parent_id=parent_id)
            except (ValueError, TypeError):
                return JsonResponse({"error": "Invalid parent_id"}, status=400)

        # Сортировка
        categories = categories.order_by('order', 'name')

        # Пагинация
        paginator = Paginator(categories, page_size)
        page_obj = paginator.get_page(page)

        results = [
            {
                "id": cat.id,  # ✅ ГЛАВНОЕ: ID для фронтенда
                "code_1c": cat.code_1c,
                "name": cat.name,
                "description": cat.description,
                "parentId": cat.parent_id,  # ✅ ИЗМЕНЕНО: parentId вместо parent_code_1c
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
        category_id = request.GET.get('category')  # ✅ ИЗМЕНЕНО: category_id вместо category_code
        search = request.GET.get('search', '').strip()

        # Получаем активные товары с категориями
        products = Product.objects.filter(is_active=True).select_related('category')

        # ✅ ИЗМЕНЕНО: Фильтр по category_id
        if category_id:
            try:
                category_id = int(category_id)
                products = products.filter(category_id=category_id)
            except (ValueError, TypeError):
                return JsonResponse({"error": "Invalid category_id"}, status=400)

        # Поиск
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(full_name__icontains=search) |
                Q(code_1c__icontains=search)
            )

        # Сортировка
        products = products.order_by('name')

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
                "category": {  # ✅ ИЗМЕНЕНО: возвращаем объект категории
                    "id": prod.category.id,
                    "name": prod.category.name
                } if prod.category else None
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
            "category": {  # ✅ ИЗМЕНЕНО: упрощена структура
                "id": product.category.id,
                "name": product.category.name
            } if product.category else None,
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat()
        }

        return JsonResponse(response_data)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def category_tree(request):
    """Получение дерева категорий (БЕЗ ПАГИНАЦИИ - для особых случаев)"""
    try:
        # ✅ ИЗМЕНЕНО: Работаем через parent_id вместо parent_code_1c
        def build_tree(parent_id=None):
            if parent_id is None:
                # Корневые категории
                categories = Category.objects.filter(
                    is_active=True,
                    parent__isnull=True
                ).order_by('order', 'name')
            else:
                # Дочерние категории
                categories = Category.objects.filter(
                    is_active=True,
                    parent_id=parent_id
                ).order_by('order', 'name')

            result = []
            for cat in categories:
                cat_data = {
                    "id": cat.id,
                    "code_1c": cat.code_1c,
                    "name": cat.name,
                    "description": cat.description,
                    "parentId": cat.parent_id,  # ✅ ДОБАВЛЕНО
                    "order": cat.order,
                    "products_count": cat.products.filter(is_active=True).count(),
                    "children": build_tree(cat.id)  # ✅ ИЗМЕНЕНО: передаём id
                }
                result.append(cat_data)

            return result

        tree = build_tree()

        return JsonResponse({"categories": tree})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)