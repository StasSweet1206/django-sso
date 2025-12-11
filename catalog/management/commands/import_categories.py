"""
Команда импорта категорий из 1С
"""
import os
import requests
from requests.auth import HTTPBasicAuth
from django.core.management.base import BaseCommand
from catalog.models import Category


class Command(BaseCommand):
    help = 'Импорт категорий из 1С'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='URL для получения категорий из 1С'
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

    def handle(self, *args, **options):
        # Получаем настройки из .env или аргументов
        base_url = options.get('url') or os.getenv('ONEC_BASE_URL', '')
        username = options.get('username') or os.getenv('ONEC_USERNAME', '')
        password = options.get('password') or os.getenv('ONEC_PASSWORD', '')

        # Формируем полный URL
        if not base_url.endswith('/categories'):
            url = f"{base_url.rstrip('/')}/categories"
        else:
            url = base_url

        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('🚀 ИМПОРТ КАТЕГОРИЙ ИЗ 1С'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'URL: {url}')
        self.stdout.write(f'Логин: {username if username else "НЕ УКАЗАН"}\n')

        if not username or not password:
            self.stdout.write(self.style.ERROR('❌ ОШИБКА: Не указаны логин и пароль!'))
            self.stdout.write('\n📝 Добавьте в .env файл:')
            self.stdout.write('ONEC_USERNAME=ваш_логин')
            self.stdout.write('ONEC_PASSWORD=ваш_пароль')
            self.stdout.write('\nИли используйте аргументы:')
            self.stdout.write('python manage.py import_categories --username "логин" --password "пароль"')
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

            if not isinstance(data, list):
                self.stdout.write(self.style.ERROR('❌ Неверный формат данных'))
                return

            total = len(data)
            self.stdout.write(f'📦 Найдено категорий: {total}\n')

            # ЭТАП 1: Создаём/обновляем все категории
            created_count = 0
            updated_count = 0

            for category_data in data:
                category, created = Category.objects.update_or_create(
                    code_1c=category_data['code_1c'],
                    defaults={
                        'name': category_data['name'],
                        'description': category_data.get('description', ''),
                        'parent_code_1c': category_data.get('parent_id', ''),
                        'is_active': category_data.get('is_active', True),
                        'order': category_data.get('order', 0),
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f'✨ Создана: {category.name}')
                else:
                    updated_count += 1
                    self.stdout.write(f'🔄 Обновлена: {category.name}')

            # ЭТАП 2: Устанавливаем связи parent
            self.stdout.write('\n📎 Устанавливаем связи родитель-потомок...\n')

            linked_count = 0
            root_uuid = '00000000-0000-0000-0000-000000000000'

            for category in Category.objects.all():
                if category.parent_code_1c and category.parent_code_1c != root_uuid:
                    try:
                        parent = Category.objects.get(code_1c=category.parent_code_1c)
                        category.parent = parent
                        category.save(update_fields=['parent'])
                        linked_count += 1
                        self.stdout.write(f'🔗 {category.name} → {parent.name}')
                    except Category.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️  Родитель не найден для: {category.name}'
                            )
                        )

            # Итоги
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('✅ ИМПОРТ ЗАВЕРШЁН!'))
            self.stdout.write('=' * 80)
            self.stdout.write(f'✨ Создано новых: {created_count}')
            self.stdout.write(f'🔄 Обновлено: {updated_count}')
            self.stdout.write(f'🔗 Связей установлено: {linked_count}')
            self.stdout.write('=' * 80 + '\n')

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                self.stdout.write(self.style.ERROR('❌ ОШИБКА АВТОРИЗАЦИИ!'))
                self.stdout.write('Неверный логин или пароль.')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка HTTP: {e}'))
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка запроса: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())