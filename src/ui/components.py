# Импорт необходимых библиотек и модулей
import flet as ft                  # Фреймворк для создания пользовательского интерфейса
from ui.styles import AppStyles    # Импорт стилей приложения
from utils.cache import ChatCache 
import requests
import flet as ft
import random
 
# Диалог авторизации по API-ключу OpenRouter
class ApiKeyDialog(ft.AlertDialog):

    def __init__(self, page, on_success):
        super().__init__()

        self.page = page
        self.on_success = on_success
        self.cache = ChatCache()    # кэш для хранения ключа и PIN

        # Поле ввода API-ключа
        self.api_key = ft.TextField(
            label="OpenRouter API Key",
            password=True,
            can_reveal_password=True,
            width=500
        )

        # Текст ошибок
        self.error_text = ft.Text(color=ft.Colors.RED)

        self.modal = True
        self.title = ft.Text("Авторизация OpenRouter")

        # Содержимое окна
        self.content = ft.Column([self.api_key, self.error_text], tight=True)

        # Кнопка входа
        self.actions = [ft.ElevatedButton("Войти", on_click=self.login)]

    # Проверка API-ключа
    def login(self, e):
        key = self.api_key.value.strip()

        # Проверка на пустой ввод
        if not key:
            self.error_text.value = "Введите API Key"
            self.page.update()
            return

        try:
            # Запрос к OpenRouter для проверки ключа
            response = requests.get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {key}"}, timeout=10)

            if response.status_code != 200:
                self.error_text.value = "Неверный API Key"
                self.page.update()
                return

            # Генерация PIN-кода
            pin = f"{random.randint(0, 9999):04d}"

            self.cache.save_auth(key, pin)

            print(f"PIN: {pin}")  # либо показать пользователю

            self.open = False
            self.page.update()

            self.on_success(key)

        except Exception as ex:
            self.error_text.value = f"Ошибка подключения: {ex}"
            self.page.update()

# Диалог подтверждения по PIN-коду
class PinDialog(ft.AlertDialog):

    def __init__(self, page, cache, on_success, on_reset):
        super().__init__()

        self.page = page
        self.cache = cache
        self.on_success = on_success
        self.on_reset = on_reset

        # Поле ввода PIN
        self.pin_field = ft.TextField(label="PIN", password=True, max_length=4)

        self.error_text = ft.Text(color=ft.Colors.RED)

        self.title = ft.Text("Введите PIN")

        self.content = ft.Column([self.pin_field, self.error_text])

        # Кнопки входа и сброса ключа
        self.actions = [
            ft.TextButton("Сбросить ключ", on_click=self.reset_key), 
            ft.ElevatedButton("Войти", on_click=self.check_pin)]

    # Проверка PIN-кода
    def check_pin(self, e):
        saved_pin = self.cache.get_pin()

        if self.pin_field.value == saved_pin:
            self.open = False
            self.page.update()

            api_key, _ = self.cache.get_auth()
            self.on_success(api_key)
    
        else:
            self.error_text.value = "Неверный PIN"
            self.page.update()

    # Сброс сохранённых данных авторизации
    def reset_key(self, e):
        self.cache.clear_auth()

        self.open = False
        self.page.update()
        self.on_reset()


class MessageBubble(ft.Container):
    """
    Компонент "пузырька" сообщения в чате.
    
    Наследуется от ft.Container для создания стилизованного контейнера сообщения.
    Отображает сообщения пользователя и AI с разными стилями и позиционированием.
    
    Args:
        message (str): Текст сообщения для отображения
        is_user (bool): Флаг, указывающий, является ли это сообщением пользователя
    """
    def __init__(self, message: str, is_user: bool):
        # Инициализация родительского класса Container
        super().__init__()
        
        # Настройка отступов внутри пузырька
        self.padding = 10
        
        # Настройка скругления углов пузырька
        self.border_radius = 10
        
        # Установка цвета фона в зависимости от отправителя:
        # - Синий для сообщений пользователя
        # - Серый для сообщений AI
        self.bgcolor = ft.Colors.BLUE_700 if is_user else ft.Colors.GREY_700
        
        # Установка выравнивания пузырька:
        # - Справа для сообщений пользователя
        # - Слева для сообщений AI
        self.alignment = ft.alignment.center_right if is_user else ft.alignment.center_left
        
        # Настройка внешних отступов для создания эффекта диалога:
        # - Отступ слева для сообщений пользователя
        # - Отступ справа для сообщений AI
        # - Небольшие отступы сверху и снизу для разделения сообщений
        self.margin = ft.margin.only(
            left=50 if is_user else 0,      # Отступ слева
            right=0 if is_user else 50,      # Отступ справа
            top=5,                           # Отступ сверху
            bottom=5                         # Отступ снизу
        )
        
        # Создание содержимого пузырька
        self.content = ft.Column(
            controls=[
                # Текст сообщения с настройками отображения
                ft.Text(
                    value=message,                    # Текст сообщения
                    color=ft.Colors.WHITE,            # Белый цвет текста
                    size=16,                         # Размер шрифта
                    selectable=True,                 # Возможность выделения текста
                    weight=ft.FontWeight.W_400       # Нормальная толщина шрифта
                )
            ],
            tight=True  # Плотное расположение элементов в колонке
        )


class ModelSelector(ft.Dropdown):
    """
    Выпадающий список для выбора AI модели с функцией поиска.
    
    Наследуется от ft.Dropdown для создания кастомного выпадающего списка
    с дополнительным полем поиска для фильтрации моделей.
    
    Args:
        models (list): Список доступных моделей в формате:
                      [{"id": "model-id", "name": "Model Name"}, ...]
    """
    def __init__(self, models: list):
        # Инициализация родительского класса Dropdown
        super().__init__()
        
        # Применение стилей из конфигурации к компоненту
        for key, value in AppStyles.MODEL_DROPDOWN.items():
            setattr(self, key, value)
            
        # Настройка внешнего вида выпадающего списка
        self.label = None                    # Убираем текстовую метку
        self.hint_text = "Выбор модели"      # Текст-подсказка
        
        # Создание списка опций из предоставленных моделей
        self.options = [
            ft.dropdown.Option(
                key=model['id'],             # ID модели как ключ
                text=model['name']           # Название модели как отображаемый текст
            ) for model in models
        ]
        
        # Сохранение полного списка опций для фильтрации
        self.all_options = self.options.copy()
        
        # Установка начального значения (первая модель из списка)
        self.value = models[0]['id'] if models else None
        
        # Создание поля поиска для фильтрации моделей
        self.search_field = ft.TextField(
            on_change=self.filter_options,        # Функция обработки изменений
            hint_text="Поиск модели",            # Текст-подсказка в поле поиска
            **AppStyles.MODEL_SEARCH_FIELD       # Применение стилей из конфигурации
        )

    def filter_options(self, e):
        """
        Фильтрация списка моделей на основе введенного текста поиска.
        
        Args:
            e: Событие изменения текста в поле поиска
        """
        # Получение текста поиска в нижнем регистре
        search_text = self.search_field.value.lower() if self.search_field.value else ""
        
        # Если поле поиска пустое - показываем все модели
        if not search_text:
            self.options = self.all_options
        else:
            # Фильтрация моделей по тексту поиска
            # Ищем совпадения в названии или ID модели
            self.options = [
                opt for opt in self.all_options
                if search_text in opt.text.lower() or search_text in opt.key.lower()
            ]
        
        # Обновление интерфейса для отображения отфильтрованного списка
        e.page.update()
