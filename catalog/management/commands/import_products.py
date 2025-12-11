"""
Команда импорта товаров из 1С
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Product, ProductVariant, Category


class Command(BaseCommand):
    help = 'Импорт товаров из 1С'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='URL для получения товаров из 1С'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Логин для 1С'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Пароль для 1С'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Ограничение количества товаров (для теста)'
        )

    def handle(self, *args, **options):
        # Получаем настройки из .env или аргументов
        base_url = options.get('url') or os.getenv('ONEC_BASE_URL', '')
        username = options.get('username') or os.getenv('ONEC_USERNAME', '')
        password = options.get('password') or os.getenv('ONEC_PASSWORD', '')
        limit = options.get('limit')

        # Формируем полный URL
        if not base_url.endswith('/products'):
            url = f"{base_url.rstrip('/')}/products"
        else:
            url = base_url

        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('🚀 ИМПОРТ ТОВАРОВ ИЗ 1С'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'URL: {url}')
        self.stdout.write(f'Логин: {username if username else "НЕ УКАЗАН"}\n')

        if not username or not password:
            self.stdout.write(self.style.ERROR('❌ ОШИБКА: Не указаны логин и пароль!'))
            self.stdout.write('\n📝 Добавьте в .env файл:')
            self.stdout.write('ONEC_USERNAME=ваш_логин')
            self.stdout.write('ONEC_PASSWORD=ваш_пароль')
            self.stdout.write('\nИли используйте аргументы:')
            self.stdout.write('python manage.py import_products --username "логин" --password "пароль"')
            return

        try:
            # Запрос к 1С с авторизацией
            self.stdout.write('📡 Отправляем запрос к 1С с авторизацией...')

            response = requests.get(
                url,
                auth=HTTPBasicAuth(username, password),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            self.stdout.write(self.style.SUCCESS('✅ Данные получены!\n'))

            # Проверяем структуру данных
            if not isinstance(data, list):
                self.stdout.write(self.style.ERROR('❌ Неверный формат данных (ожидается список)'))
                self.stdout.write(f'Получено: {type(data)}')
                return

            products_data = data[:limit] if limit else data
            total = len(products_data)

            self.stdout.write(f'📦 Найдено товаров: {total}\n')

            # Импорт товаров
            created_count = 0
            updated_count = 0
            error_count = 0
            variants_created = 0
            variants_updated = 0

            for index, product_data in enumerate(products_data, 1):
                try:
                    result = self._import_product(product_data)

                    if result['product'] == 'created':
                        created_count += 1
                    elif result['product'] == 'updated':
                        updated_count += 1

                    variants_created += result.get('variants_created', 0)
                    variants_updated += result.get('variants_updated', 0)

                    # Прогресс
                    if index % 10 == 0 or index == total:
                        self.stdout.write(f'⏳ Обработано: {index}/{total}')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'❌ [{index}] Ошибка при импорте товара: {e}')
                    )

            # Итоги
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('✅ ИМПОРТ ЗАВЕРШЁН!'))
            self.stdout.write('=' * 80)
            self.stdout.write(f'📦 Товары:')
            self.stdout.write(f'  ✨ Создано новых: {created_count}')
            self.stdout.write(f'  🔄 Обновлено: {updated_count}')
            self.stdout.write(f'🎨 Варианты товаров:')
            self.stdout.write(f'  ✨ Создано новых: {variants_created}')
            self.stdout.write(f'  🔄 Обновлено: {variants_updated}')
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'⚠️  Ошибок: {error_count}'))
            self.stdout.write('=' * 80 + '\n')

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Ошибка запроса к 1С: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Неожиданная ошибка: {e}'))

    @transaction.atomic
    def _import_product(self, data):
        """Импорт одного товара с вариантами"""

        # Получаем код 1С товара
        code_1c = data.get('code_1c') or data.get('id') or data.get('external_id')
        if not code_1c:
            raise ValueError('Не указан code_1c товара')

        # Получаем категорию
        category = None
        category_code = data.get('category_code_1c') or data.get('category_id')
        if category_code:
            try:
                category = Category.objects.get(code_1c=str(category_code))
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Категория {category_code} не найдена')
                )

        # Создаем или обновляем товар
        product, created = Product.objects.update_or_create(
            code_1c=str(code_1c),
            defaults={
                'name': data.get('name', 'Без названия'),
                'full_name': data.get('full_name', data.get('name', '')),
                'category': category,
                'image_url': data.get('image_url', ''),
                'has_variants': data.get('has_variants', False),
                'is_active': data.get('is_active', True),
            }
        )

        result = {
            'product': 'created' if created else 'updated',
            'variants_created': 0,
            'variants_updated': 0
        }

        # Импортируем варианты товара
        variants = data.get('variants', [])
        if variants:
            for variant_data in variants:
                variant_code = variant_data.get('code_1c')
                if not variant_code:
                    continue

                # category_id в варианте = code_1c родительского продукта
                variant, variant_created = ProductVariant.objects.update_or_create(
                    code_1c=str(variant_code),
                    defaults={
                        'product': product,  # Связь с родительским товаром
                        'name': variant_data.get('name', ''),
                        'full_name': variant_data.get('full_name', ''),
                        'image_url': variant_data.get('image_url', ''),
                        'is_active': variant_data.get('is_active', True),
                    }
                )

                if variant_created:
                    result['variants_created'] += 1
                else:
                    result['variants_updated'] += 1

        return result