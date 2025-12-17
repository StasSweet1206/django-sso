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
        parent_id = request.GET.get('parent_id')

        print(f"🔍 categories_list: parent_id={parent_id}, page={page}, page_size={page_size}")

        # Получаем только активные категории
        categories = Category.objects.filter(is_active=True)

        if parent_id == 'root' or parent_id == 'null' or not parent_id:
            categories = categories.filter(parent__isnull=True)
            print(f"📂 Загружаем КОРНЕВЫЕ категории")
        else:
            try:
                parent_id_int = int(parent_id)
                categories = categories.filter(parent_id=parent_id_int)
                print(f"📂 Загружаем ПОДКАТЕГОРИИ для parent_id={parent_id_int}")
            except (ValueError, TypeError):
                print(f"❌ Неверный parent_id: {parent_id}")
                return JsonResponse({"error": "Invalid parent_id"}, status=400)

        categories = categories.order_by('order', 'name')
        print(f"📊 Найдено категорий ПЕРЕД пагинацией: {categories.count()}")

        # Пагинация
        paginator = Paginator(categories, page_size)
        page_obj = paginator.get_page(page)
        print(f"📄 Страница {page}/{paginator.num_pages}, товаров на странице: {len(page_obj)}")

        results = []
        for cat in page_obj:
            result = {
                "id": cat.id,
                "code_1c": cat.code_1c,
                "name": cat.name,
                "description": cat.description,
                "parent": cat.parent_id,
                "parent_id": cat.parent_id,
                "parent_code_1c": cat.parent.code_1c if cat.parent_id else None,  # ✅ БЕЗОПАСНО
                "image": cat.image.url if cat.image else None,  # ✅ ДОБАВЛЕНО
                "has_children": cat.children.filter(is_active=True).exists(),
                "products_count": cat.products.filter(is_active=True).count(),
                "order": cat.order
            }
            results.append(result)
            print(f"  ✅ ID: {cat.id}, NAME: {cat.name}, PARENT: {cat.parent_id}, IMAGE: {result['image']}")

        response_data = {
            "results": results,
            "count": paginator.count,
            "next": page_obj.next_page_number() if page_obj.has_next() else None,
            "previous": page_obj.previous_page_number() if page_obj.has_previous() else None
        }

        print(f"✅ Отправляем {len(results)} категорий")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"❌ ОШИБКА в categories_list: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def products_list(request):
    """Получение списка товаров"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        category_id = request.GET.get('category')
        search = request.GET.get('search', '').strip()

        print(f"🔍 products_list: category_id={category_id}, search={search}, page={page}")

        # Получаем активные товары с категориями
        products = Product.objects.filter(is_active=True).select_related('category')

        # ✅ ИЗМЕНЕНО: Фильтр по category_id
        if category_id:
            try:
                category_id_int = int(category_id)
                products = products.filter(category_id=category_id_int)
                print(f"📂 Фильтруем по category_id={category_id_int}")
            except (ValueError, TypeError):
                print(f"❌ Неверный category_id: {category_id}")
                return JsonResponse({"error": "Invalid category_id"}, status=400)

        # Поиск
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(full_name__icontains=search) |
                Q(code_1c__icontains=search)
            )
            print(f"🔎 Поиск по запросу: {search}")

        # Сортировка
        products = products.order_by('name')

        print(f"📊 Найдено товаров ПЕРЕД пагинацией: {products.count()}")

        # Пагинация
        paginator = Paginator(products, page_size)
        page_obj = paginator.get_page(page)

        print(f"📄 Страница {page}/{paginator.num_pages}, товаров на странице: {len(page_obj)}")
        
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
                "category": {
                    "id": prod.category.id,
                    "name": prod.category.name,
                    "code_1c": prod.category.code_1c  # ✅ ДОБАВЛЕНО
                } if prod.category else None
            }
            results.append(product_data)

        print(f"✅ Отправляем {len(results)} товаров")

        return JsonResponse({
            "results": results,
            "count": paginator.count,
            "next": page_obj.next_page_number() if page_obj.has_next() else None,
            "previous": page_obj.previous_page_number() if page_obj.has_previous() else None
        })
    except Exception as e:
        print(f"❌ ОШИБКА в products_list: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def product_detail(request, product_id):
    """Получение детальной информации о товаре"""
    try:
        print(f"🔍 product_detail: product_id={product_id}")

        product = Product.objects.select_related('category').prefetch_related(
            Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True))
        ).get(id=product_id, is_active=True)

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
            "category": {
                "id": product.category.id,
                "name": product.category.name,
                "code_1c": product.category.code_1c  # ✅ ДОБАВЛЕНО
            } if product.category else None,
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat()
        }

        print(f"✅ Товар найден: {product.name}, вариантов: {len(variants)}")
        return JsonResponse(response_data)

    except Product.DoesNotExist:
        print(f"❌ Товар не найден: {product_id}")
        return JsonResponse({"error": "Товар не найден"}, status=404)
    except Exception as e:
        print(f"❌ ОШИБКА в product_detail: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

# ✅ ДОБАВЛЕНО: Endpoint для получения подкатегорий конкретной категории
@csrf_exempt
@require_http_methods(["GET"])
def category_subcategories(request, category_id):
    """Получение прямых подкатегорий для категории"""
    try:
        print(f"🔍 category_subcategories: category_id={category_id}")

        # Проверяем существование родительской категории
        try:
            parent_category = Category.objects.get(id=category_id, is_active=True)
            print(f"✅ Родительская категория: {parent_category.name}")
        except Category.DoesNotExist:
            print(f"❌ Категория не найдена: {category_id}")
            return JsonResponse({"error": "Категория не найдена"}, status=404)

        # Получаем подкатегории
        subcategories = Category.objects.filter(
            parent_id=category_id,
            is_active=True
        ).order_by('order', 'name')

        print(f"📊 Найдено подкатегорий: {subcategories.count()}")

        results = []
        for cat in subcategories:
            result = {
                "id": cat.id,
                "code_1c": cat.code_1c,
                "name": cat.name,
                "description": cat.description,
                "parent": cat.parent_id,
                "parent_id": cat.parent_id,
                "parent_code_1c": cat.parent.code_1c if cat.parent_id else None,  # ✅ БЕЗОПАСНО
                "image": cat.image.url if cat.image else None,  # ✅ ДОБАВЛЕНО
                "has_children": cat.children.filter(is_active=True).exists(),
                "products_count": cat.products.filter(is_active=True).count(),
                "order": cat.order
            }
            results.append(result)
            print(f"  ✅ ID: {cat.id}, NAME: {cat.name}, PARENT: {cat.parent_id}, IMAGE: {result['image']}")

        print(f"✅ Отправляем {len(results)} подкатегорий")
        return JsonResponse({"results": results, "count": len(results)})

    except Exception as e:
        print(f"❌ ОШИБКА в category_subcategories: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)