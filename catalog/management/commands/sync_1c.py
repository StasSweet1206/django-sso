"""
Management команда для синхронизации с 1С
"""
from django.core.management.base import BaseCommand
from catalog.services.onec_sync import onec_sync


class Command(BaseCommand):
    """Команда синхронизации данных с 1С"""

    help = 'Синхронизация данных с 1С'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            action='store_true',
            help='Синхронизировать только категории'
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('СИНХРОНИЗАЦИЯ С 1С')
        self.stdout.write('=' * 50)
        self.stdout.write('')

        if options['categories']:
            self._sync_categories()
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Укажите --categories для синхронизации'
                )
            )

    def _sync_categories(self):
        """Синхронизация категорий"""
        self.stdout.write('Синхронизация категорий...')
        self.stdout.write('')

        result = onec_sync.sync_categories()

        # Статистика
        self.stdout.write(
            self.style.SUCCESS(
                f"Всего обработано: {result['total']}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Создано новых: {result['created']}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Обновлено: {result['updated']}"
            )
        )

        # Ошибки
        if result['errors']:
            self.stdout.write('')
            self.stdout.write(
                self.style.ERROR(
                    f"Ошибок: {len(result['errors'])}"
                )
            )
            for error in result['errors']:
                self.stdout.write(self.style.ERROR(f"  - {error}"))

        self.stdout.write('')
        self.stdout.write('=' * 50)