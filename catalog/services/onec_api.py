"""
API для работы с 1С
"""
import logging
from typing import List, Dict
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OneCAPI:
    """API для работы с 1С"""

    def __init__(self):
        self.base_url = getattr(settings, 'ONEC_API_URL', '')
        self.login = getattr(settings, 'ONEC_API_LOGIN', '')
        self.password = getattr(settings, 'ONEC_API_PASSWORD', '')
        self.test_mode = getattr(settings, 'ONEC_TEST_MODE', False)

        self.session = requests.Session()
        self.session.auth = (self.login, self.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def get_categories(self) -> List[Dict]:
        """
        Получить список категорий из 1С

        Returns:
            List[Dict]: Список категорий
        """
        # Если тестовый режим - возвращаем тестовые данные
        if self.test_mode:
            return self._get_test_categories()

        try:
            url = f"{self.base_url}/categories"
            logger.info("Запрос категорий: %s", url)

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.info("Получено категорий: %s", len(data))

            return data

        except requests.exceptions.RequestException as error:
            logger.error("Ошибка при получении категорий: %s", error)
            return []
        except Exception as error:
            logger.error("Неожиданная ошибка: %s", error)
            return []

    def _get_test_categories(self) -> List[Dict]:
        """Тестовые данные категорий для отладки"""
        return [
            {
                'id': 'cat_001',
                'name': 'Электроника',
                'description': 'Электронные товары',
                'parent_id': None
            },
            {
                'id': 'cat_002',
                'name': 'Смартфоны',
                'description': 'Мобильные телефоны',
                'parent_id': 'cat_001'
            },
            {
                'id': 'cat_003',
                'name': 'Ноутбуки',
                'description': 'Портативные компьютеры',
                'parent_id': 'cat_001'
            },
            {
                'id': 'cat_004',
                'name': 'Одежда',
                'description': 'Одежда и аксессуары',
                'parent_id': None
            },
            {
                'id': 'cat_005',
                'name': 'Мужская одежда',
                'description': 'Одежда для мужчин',
                'parent_id': 'cat_004'
            },
        ]