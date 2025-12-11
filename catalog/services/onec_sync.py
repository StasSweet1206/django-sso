"""
Сервис синхронизации данных с 1С
"""
import logging
from typing import Dict, List
from django.db import transaction
from catalog.models import Category
from .onec_api import OneCAPI

logger = logging.getLogger(__name__)


class OneCSync:
    """Синхронизация данных с 1С"""

    def __init__(self):
        self.api = OneCAPI()

    def sync_categories(self) -> Dict:
        """
        Синхронизация категорий из 1С

        Returns:
            Dict: Статистика синхронизации
        """
        result = {
            'created': 0,
            'updated': 0,
            'errors': [],
            'total': 0
        }

        try:
            # Получаем категории из 1С
            logger.info("Начало синхронизации категорий...")
            categories_data = self.api.get_categories()
            result['total'] = len(categories_data)

            if not categories_data:
                logger.warning("Нет данных для синхронизации")
                return result

            # Сначала синхронизируем родительские категории
            parent_categories = [
                c for c in categories_data if not c.get('parent_id')
            ]
            self._sync_category_batch(parent_categories, result)

            # Затем дочерние категории
            child_categories = [
                c for c in categories_data if c.get('parent_id')
            ]
            self._sync_category_batch(child_categories, result)

            logger.info(
                "Синхронизация завершена: создано %s, обновлено %s",
                result['created'],
                result['updated']
            )

        except Exception as error:
            error_msg = f"Критическая ошибка синхронизации: {error}"
            logger.error(error_msg)
            result['errors'].append(error_msg)

        return result

    def _sync_category_batch(
        self,
        categories: List[Dict],
        result: Dict
    ):
        """
        Синхронизация пакета категорий

        Args:
            categories: Список категорий для синхронизации
            result: Словарь со статистикой (модифицируется)
        """
        for cat_data in categories:
            try:
                with transaction.atomic():
                    self._sync_single_category(cat_data, result)
            except Exception as error:
                error_msg = (
                    f"Ошибка категории "
                    f"'{cat_data.get('name')}': {error}"
                )
                logger.error(error_msg)
                result['errors'].append(error_msg)

    def _sync_single_category(self, cat_data: Dict, result: Dict):
        """
        Синхронизация одной категории

        Args:
            cat_data: Данные категории из 1С
            result: Словарь со статистикой (модифицируется)
        """
        # Ищем родительскую категорию
        parent = None
        if cat_data.get('parent_id'):
            try:
                parent = Category.objects.get(
                    external_id=cat_data['parent_id']
                )
            except Category.DoesNotExist:
                logger.warning(
                    "Родительская категория %s не найдена",
                    cat_data['parent_id']
                )

        # Создаем или обновляем категорию
        category, created = Category.objects.update_or_create(
            external_id=cat_data['id'],
            defaults={
                'name': cat_data['name'],
                'description': cat_data.get('description', ''),
                'parent': parent,
                'is_active': True
            }
        )

        if created:
            result['created'] += 1
            logger.info("Создана категория: %s", category.name)
        else:
            result['updated'] += 1
            logger.info("Обновлена категория: %s", category.name)


# Создаем глобальный экземпляр
onec_sync = OneCSync()