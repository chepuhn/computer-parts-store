#!/usr/bin/env python3
"""
Telegram бот магазина компьютерных комплектующих с Web App интерфейсом
Курсовая работа
Автор: [Ваше ФИО]
Группа: [Ваша группа]
"""

import sqlite3
import telebot
import json
from telebot import types
import os
import logging
from datetime import datetime
import config  # Импорт конфигурации

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parts_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = config.BOT_TOKEN
DB_PATH = config.DB_PATH
WEB_APP_URL = config.WEB_APP_URL
BOT_NAME = config.BOT_NAME
BOT_VERSION = config.BOT_VERSION

# Проверка токена
if not TOKEN or ':' not in TOKEN:
    logger.error("❌ Неправильный формат токена!")
    print("❌ ОШИБКА: Добавьте токен в файл .env")
    exit(1)

# Инициализация бота
bot = telebot.TeleBot(TOKEN)
print("=" * 60)
print(f"🖥️ {BOT_NAME} v{BOT_VERSION}")
print("=" * 60)
print(f"🌐 Web App URL: {WEB_APP_URL}")
print(f"📁 База данных: {DB_PATH}")


# ========== ФУНКЦИИ БАЗЫ ДАННЫХ ==========

def init_database():
    """Инициализация базы данных компьютерных комплектующих"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("📊 Создание таблиц базы данных...")

        # Таблица категорий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            icon TEXT,
            slug TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Таблица товаров
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            category_id INTEGER NOT NULL,
            image_url TEXT,
            specs TEXT,
            in_stock BOOLEAN DEFAULT TRUE,
            rating REAL DEFAULT 0,
            brand TEXT,
            stock_quantity INTEGER DEFAULT 0,
            popularity INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        ''')

        # Таблица заказов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            user_phone TEXT,
            products TEXT,
            total_price REAL,
            status TEXT DEFAULT 'pending',
            address TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            total_orders INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0,
            last_activity TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Проверяем наличие данных в категориях
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            print("📝 Заполняем таблицу категорий...")
            categories_data = [
                ('Процессоры', 'Центральные процессоры (CPU) для компьютеров', '⚡', 'cpu'),
                ('Видеокарты', 'Графические процессоры (GPU) для игр и работы', '🎮', 'gpu'),
                ('Материнские платы', 'Системные платы для сборки ПК', '🖥️', 'motherboards'),
                ('Оперативная память', 'Модули RAM для увеличения производительности', '💾', 'ram'),
                ('Накопители', 'SSD и HDD накопители для хранения данных', '💿', 'storage'),
                ('Блоки питания', 'Источники питания (PSU) для стабильной работы', '🔌', 'psu'),
                ('Корпуса', 'Корпуса для ПК различных форм-факторов', '📦', 'cases'),
                ('Охлаждение', 'Системы охлаждения для процессоров и корпусов', '❄️', 'cooling'),
                ('Мониторы', 'Мониторы и дисплеи различных диагоналей', '🖥️', 'monitors'),
                ('Клавиатуры', 'Клавиатуры механические и мембранные', '⌨️', 'keyboards'),
                ('Мыши', 'Игровые и офисные компьютерные мыши', '🖱️', 'mice'),
                ('Аудио', 'Наушники, колонки и аудиосистемы', '🎧', 'audio'),
                ('Сеть', 'Сетевые карты, роутеры и оборудование', '🌐', 'network')
            ]
            cursor.executemany(
                "INSERT INTO categories (name, description, icon, slug) VALUES (?, ?, ?, ?)",
                categories_data
            )
            print(f"✅ Добавлено {len(categories_data)} категорий")

        # Получаем ID категорий для заполнения товаров
        cursor.execute("SELECT id, slug FROM categories")
        category_map = {slug: id for id, slug in cursor.fetchall()}

        # Проверяем наличие товаров
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            print("📝 Заполняем таблицу товаров...")
            products_data = [
                # Процессоры
                ('AMD Ryzen 5 7600X', '6-ядерный процессор для игр и работы', 24999.0,
                 category_map['cpu'], 'https://example.com/cpu1.jpg',
                 'Сокет: AM5 | Ядра: 6 | Потоки: 12 | Частота: 4.7-5.3 ГГц | Кэш L3: 32 МБ | TDP: 105W',
                 True, 4.8, 'AMD', 15, 120),
                ('Intel Core i5-13400F', 'Процессор для офиса и игр', 19850.0,
                 category_map['cpu'], 'https://example.com/cpu2.jpg',
                 'Сокет: LGA1700 | Ядра: 10 (6P+4E) | Потоки: 16 | Частота: 2.5-4.6 ГГц | TDP: 65W',
                 True, 4.6, 'Intel', 8, 95),
                ('AMD Ryzen 7 7800X3D', 'Игровой процессор с технологией 3D V-Cache', 37999.0,
                 category_map['cpu'], 'https://example.com/cpu3.jpg',
                 'Сокет: AM5 | Ядра: 8 | Потоки: 16 | Частота: 4.2-5.0 ГГц | Кэш L3: 96 МБ | TDP: 120W',
                 True, 4.9, 'AMD', 5, 75),

                # Видеокарты
                ('ASUS TUF RTX 4060 Ti', 'Игровая видеокарта для Full HD/2K игр', 48990.0,
                 category_map['gpu'], 'https://example.com/gpu1.jpg',
                 'Память: 8 ГБ GDDR6 | Частота: 2310 МГц | Разъемы: 3xDP, 1xHDMI | Длина: 300 мм | Питание: 8-pin',
                 True, 4.7, 'ASUS', 12, 150),
                ('GIGABYTE RX 7700 XT', 'Видеокарта для 1440p игр', 42999.0,
                 category_map['gpu'], 'https://example.com/gpu2.jpg',
                 'Память: 12 ГБ GDDR6 | Частота: 2171 МГц | Разъемы: 3xDP, 1xHDMI | Длина: 320 мм',
                 True, 4.6, 'GIGABYTE', 7, 85),

                # Материнские платы
                ('ASUS ROG STRIX B650-A', 'Игровая материнская плата AM5', 21999.0,
                 category_map['motherboards'], 'https://example.com/mb1.jpg',
                 'Сокет: AM5 | Форм-фактор: ATX | Память: DDR5 | Слоты M.2: 3 | Wi-Fi: Да | Bluetooth: 5.2',
                 True, 4.8, 'ASUS', 10, 110),
                ('MSI PRO B760-P', 'Материнская плата для офисных сборок', 14999.0,
                 category_map['motherboards'], 'https://example.com/mb2.jpg',
                 'Сокет: LGA1700 | Форм-фактор: ATX | Память: DDR4 | Слоты M.2: 2 | Wi-Fi: Нет',
                 True, 4.5, 'MSI', 15, 65),

                # Оперативная память
                ('Kingston FURY Beast 32GB', 'Оперативная память DDR5 для игровых систем', 7850.0,
                 category_map['ram'], 'https://example.com/ram1.jpg',
                 'Объем: 32 ГБ (2x16) | Частота: 6000 МГц | Тайминги: CL36 | Напряжение: 1.35В | RGB: Да',
                 True, 4.7, 'Kingston', 25, 140),
                ('Corsair Vengeance 16GB', 'Игровая память RGB подсветкой', 5990.0,
                 category_map['ram'], 'https://example.com/ram2.jpg',
                 'Объем: 16 ГБ (2x8) | Частота: 3600 МГц | Тайминги: CL18 | Подсветка: RGB iCUE',
                 True, 4.6, 'Corsair', 30, 125),

                # Накопители
                ('Samsung 980 Pro 1TB', 'NVMe SSD накопитель PCIe 4.0', 9990.0,
                 category_map['storage'], 'https://example.com/ssd1.jpg',
                 'Форм-фактор: M.2 2280 | Интерфейс: PCIe 4.0 | Скорость чтения: 7000 МБ/с | Запись: 5000 МБ/с | TBW: 600',
                 True, 4.9, 'Samsung', 20, 180),
                ('WD Blue SN580 2TB', 'Игровой SSD с высокими скоростями', 12990.0,
                 category_map['storage'], 'https://example.com/ssd2.jpg',
                 'Форм-фактор: M.2 2280 | Интерфейс: PCIe 4.0 | Скорость чтения: 4150 МБ/с | TBW: 900',
                 True, 4.7, 'Western Digital', 12, 95),

                # Блоки питания
                ('be quiet! Pure Power 12 750W', 'Мощный и тихий блок питания', 10390.0,
                 category_map['psu'], 'https://example.com/psu1.jpg',
                 'Мощность: 750 Вт | Сертификат: 80+ Gold | Модульный: Полумодульный | Вентилятор: 120 мм | Гарантия: 5 лет',
                 True, 4.8, 'be quiet!', 8, 70),

                # Корпуса
                ('NZXT H5 Flow', 'Корпус с отличной системой охлаждения', 7200.0,
                 category_map['cases'], 'https://example.com/case1.jpg',
                 'Форм-фактор: Mid-Tower | Материал: Сталь, стекло | Вентиляторы: 2x120 мм | Подсветка: Нет | USB: 2xUSB 3.0',
                 True, 4.6, 'NZXT', 10, 85),

                # Охлаждение
                ('DeepCool AK620', 'Башенный кулер для мощных процессоров', 5499.0,
                 category_map['cooling'], 'https://example.com/cooler1.jpg',
                 'Тип: Воздушное | TDP: 260 Вт | Вентиляторы: 2x120 мм | Высота: 160 мм | Подсветка: Нет | Совместимость: AM5/LGA1700',
                 True, 4.7, 'DeepCool', 15, 60),

                # Мониторы
                ('Samsung Odyssey G5', 'Игровой монитор с изогнутым экраном', 29990.0,
                 category_map['monitors'], 'https://example.com/monitor1.jpg',
                 'Диагональ: 27" | Разрешение: 2560x1440 | Частота: 144 Гц | Панель: VA | Изгиб: 1000R | Отклик: 1ms',
                 True, 4.8, 'Samsung', 6, 110),

                # Клавиатуры
                ('Logitech G Pro X', 'Механическая игровая клавиатура TKL', 11990.0,
                 category_map['keyboards'], 'https://example.com/kb1.jpg',
                 'Тип: Механическая | Переключатели: GX Brown (сменные) | Подсветка: RGB | Формат: TKL | Программируемые клавиши: Да',
                 True, 4.7, 'Logitech', 18, 130),

                # Мыши
                ('Razer DeathAdder V3', 'Игровая мышь для профессиональных геймеров', 8990.0,
                 category_map['mice'], 'https://example.com/mouse1.jpg',
                 'Тип: Проводная | DPI: 30000 | Кнопки: 8 | Вес: 59 г | Сенсор: Focus Pro 30K | Частота опроса: 8000 Гц',
                 True, 4.8, 'Razer', 22, 145)
            ]

            cursor.executemany('''
                INSERT INTO products (name, description, price, category_id, image_url, specs, 
                                    in_stock, rating, brand, stock_quantity, popularity) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', products_data)
            print(f"✅ Добавлено {len(products_data)} товаров")

        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации БД: {e}")
        return False


def get_db_connection():
    """Создание соединения с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def update_user_activity(user_id, username, first_name, last_name):
    """Обновление активности пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            cursor.execute(
                "UPDATE users SET last_activity = ?, username = ?, first_name = ?, last_name = ? WHERE user_id = ?",
                (now, username, first_name, last_name, user_id)
            )
        else:
            cursor.execute(
                """INSERT INTO users (user_id, username, first_name, last_name, last_activity) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, username, first_name, last_name, now)
            )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Ошибка обновления пользователя: {e}")
        return False


def get_store_statistics():
    """Получение статистики магазина"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products WHERE in_stock = 1")
        in_stock_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT brand) FROM products")
        total_brands = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM categories")
        total_categories = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM products")
        price_stats = cursor.fetchone()
        min_price, max_price, avg_price = price_stats

        conn.close()

        return {
            'total_products': total_products,
            'in_stock_products': in_stock_products,
            'total_brands': total_brands,
            'total_categories': total_categories,
            'total_orders': total_orders,
            'total_users': total_users,
            'min_price': min_price,
            'max_price': max_price,
            'avg_price': avg_price
        }

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return None


def create_order(user_id, user_name, products_data, total_price, address="", phone="", notes=""):
    """Создание нового заказа"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Преобразуем продукты в строку
        products_str = json.dumps(products_data)

        cursor.execute("""
            INSERT INTO orders (user_id, user_name, user_phone, products, total_price, status, address, notes)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (user_id, user_name, phone, products_str, total_price, address, notes))

        order_id = cursor.lastrowid

        # Обновляем статистику пользователя
        cursor.execute("""
            UPDATE users 
            SET total_orders = total_orders + 1, 
                total_spent = total_spent + ?,
                last_activity = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (total_price, user_id))

        conn.commit()
        conn.close()

        logger.info(f"✅ Создан заказ #{order_id} для пользователя {user_id}")
        return order_id

    except Exception as e:
        logger.error(f"Ошибка создания заказа: {e}")
        return None


# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение"""
    user = message.from_user
    logger.info(f"Пользователь {user.id} запустил бота")

    update_user_activity(user.id, user.username, user.first_name, user.last_name)

    welcome_text = f"""
🖥️ *Добро пожаловать в {BOT_NAME}!* v{BOT_VERSION}

*Мы предлагаем:*
• 🛒 200+ компьютерных комплектующих
• 📱 Современный Web-интерфейс
• 🔍 Умный поиск по категориям
• ⭐ Честные рейтинги и отзывы
• 🚀 Быстрая доставка по городу

*Категории товаров:*
1. ⚡ Процессоры
2. 🎮 Видеокарты
3. 🖥️ Материнские платы
4. 💾 Оперативная память
5. 💿 Накопители
6. 🔌 Блоки питания
7. 📦 Корпуса
8. ❄️ Охлаждение
9. 🖥️ Мониторы
10. ⌨️ Клавиатуры и мыши

*Начните с Web App для удобного выбора!*
    """

    web_app = types.WebAppInfo(url=WEB_APP_URL)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    web_app_btn = types.KeyboardButton(
        text="🛒 Открыть каталог товаров",
        web_app=web_app
    )

    keyboard.add(web_app_btn)
    keyboard.add(types.KeyboardButton('📁 Категории'), types.KeyboardButton('🔍 Поиск'))
    keyboard.add(types.KeyboardButton('📊 Статистика'), types.KeyboardButton('🆘 Помощь'))
    keyboard.add(types.KeyboardButton('⭐ Топ товары'), types.KeyboardButton('📞 Контакты'))

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    """Справка по боту"""
    stats = get_store_statistics()

    help_text = f"""
🆘 *Справка по {BOT_NAME}*

*Основные команды:*
/start - Главное меню
/help - Эта справка
/stats - Статистика магазина
/search - Поиск товаров
/top - Топ товаров
/categories - Все категории
/web - Web App интерфейс

*Категории товаров:*
• ⚡ Процессоры (CPU)
• 🎮 Видеокарты (GPU)
• 🖥️ Материнские платы
• 💾 Оперативная память (RAM)
• 💿 Накопители (SSD/HDD)
• 🔌 Блоки питания (PSU)
• 📦 Корпуса
• ❄️ Охлаждение
• 🖥️ Мониторы
• ⌨️ Клавиатуры и мыши

*Поиск товаров:*
• По названию
• По бренду
• По категории
• По цене

*Примеры команд:*
`/search RTX 4060`
`/search AMD Ryzen`
`/search процессор`

*Информация о магазине:*
• Товаров в наличии: {stats['in_stock_products'] if stats else 'N/A'}
• Категорий: {stats['total_categories'] if stats else 'N/A'}
• Брендов: {stats['total_brands'] if stats else 'N/A'}
    """

    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Статистика магазина"""
    stats = get_store_statistics()

    if not stats:
        bot.send_message(message.chat.id, "❌ Ошибка получения статистики")
        return

    in_stock_percentage = (stats['in_stock_products'] / stats['total_products'] * 100) if stats[
                                                                                              'total_products'] > 0 else 0

    response = f"""
📊 *Статистика магазина {BOT_NAME}:*

*Товары:*
• Всего товаров: *{stats['total_products']}*
• В наличии: *{stats['in_stock_products']}* ({in_stock_percentage:.1f}%)
• Брендов: *{stats['total_brands']}*
• Категорий: *{stats['total_categories']}*

*Цены:*
• Минимальная: *{stats['min_price']:,.0f}₽*
• Максимальная: *{stats['max_price']:,.0f}₽*
• Средняя: *{stats['avg_price']:,.0f}₽*

*Пользователи:*
• Всего пользователей: *{stats['total_users']}*
• Всего заказов: *{stats['total_orders']}*

*Техническая информация:*
• Версия бота: {BOT_VERSION}
• Web App: `{WEB_APP_URL}`
• База данных: SQLite
• Логирование: parts_bot.log

*Рекомендация:* Используйте Web App для удобного заказа!
    """

    bot.send_message(message.chat.id, response, parse_mode='Markdown')


@bot.message_handler(commands=['search'])
def search_command(message):
    """Команда поиска"""
    msg = bot.send_message(
        message.chat.id,
        "🔍 *Введите запрос для поиска товаров:*\n\n"
        "Можно искать по:\n"
        "• Названию товара\n"
        "• Бренду (ASUS, AMD, Intel и т.д.)\n"
        "• Категории (процессор, видеокарта)\n"
        "• Характеристикам (DDR5, PCIe 4.0)",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, search_products)


@bot.message_handler(commands=['top'])
def top_command(message):
    """Топ-10 товаров по рейтингу"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name, p.price, p.rating, p.brand, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.rating > 0 
            ORDER BY p.rating DESC, p.popularity DESC 
            LIMIT 10
        """)

        products = cursor.fetchall()
        conn.close()

        if not products:
            bot.send_message(message.chat.id, "❌ Нет данных о рейтингах")
            return

        response = "🏆 *Топ-10 товаров по рейтингу:*\n\n"

        for i, product in enumerate(products, 1):
            stars = "⭐" * int(product['rating'])
            if product['rating'] % 1 >= 0.5:
                stars += "½"

            response += f"*{i}. {product['name']}*\n"
            response += f"   🏷️ {product['brand']} | 📁 {product['category_name']}\n"
            response += f"   💰 {product['price']:,.0f}₽\n"
            response += f"   ⭐ {stars} ({product['rating']}/5)\n\n"

        response += "*Используйте /search для поиска других товаров*"

        bot.send_message(message.chat.id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка получения топа: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка получения рейтингов")


@bot.message_handler(commands=['categories'])
def categories_command(message):
    """Список всех категорий"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.name, c.description, c.icon, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY c.name
        """)

        categories = cursor.fetchall()
        conn.close()

        response = "📁 *Все категории компьютерных комплектующих:*\n\n"

        for category in categories:
            response += f"• {category['icon']} *{category['name']}*\n"
            response += f"  {category['description']}\n"
            response += f"  📦 Товаров: {category['product_count']}\n\n"

        response += f"*Всего категорий: {len(categories)}*\n"
        response += "*Для подробного просмотра используйте Web App!*"

        bot.send_message(message.chat.id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка получения категорий: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка получения категорий")


@bot.message_handler(commands=['web'])
def web_command(message):
    """Прямая ссылка на Web App"""
    web_app = types.WebAppInfo(url=WEB_APP_URL)

    keyboard = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton(
        text="🛒 Открыть каталог товаров",
        web_app=web_app
    )
    keyboard.add(web_btn)

    response = f"""
📱 *Web App интерфейс {BOT_NAME}*

Для удобного доступа к каталогу товаров используйте наш Web App:

*Преимущества:*
• 🎨 Визуальный интерфейс с фотографиями
• 🛒 Удобный выбор категорий
• 🔍 Быстрый поиск и фильтрация
• ⭐ Просмотр рейтингов и отзывов
• 📝 Детальные характеристики товаров
• 🛍️ Корзина и оформление заказа

*Нажмите кнопку ниже для открытия:*
    """

    bot.send_message(
        message.chat.id,
        response,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


# ========== ОБРАБОТКА WEB APP ==========

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    """Обработка данных из Web App"""
    try:
        user = message.from_user
        web_app_data = json.loads(message.web_app_data.data)
        action = web_app_data.get('action')

        logger.info(f"Web App данные от {user.id}: {action}")

        if action == 'get_categories':
            send_categories_list(message.chat.id)

        elif action == 'get_products_by_category':
            category_slug = web_app_data.get('category')
            send_products_by_category(message.chat.id, category_slug)

        elif action == 'get_product_details':
            product_id = web_app_data.get('product_id')
            send_product_details(message.chat.id, product_id)

        elif action == 'search_products':
            query = web_app_data.get('query')
            search_products_web(message.chat.id, query)

        elif action == 'get_top_products':
            send_top_products(message.chat.id)

        elif action == 'create_order':
            order_data = web_app_data.get('order_data')
            create_order_web(message.chat.id, user, order_data)

        elif action == 'test':
            bot.send_message(
                message.chat.id,
                f"✅ Web App подключен!\nДействие: {web_app_data.get('message', 'test')}"
            )

        else:
            bot.send_message(message.chat.id, "✅ Данные получены от Web App")

    except Exception as e:
        logger.error(f"Ошибка обработки Web App данных: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка обработки запроса")


def send_categories_list(chat_id):
    """Отправка списка категорий"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.name, c.description, c.icon, c.slug, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY c.name
        """)

        categories = cursor.fetchall()
        conn.close()

        if not categories:
            bot.send_message(chat_id, "❌ Категории не найдены")
            return

        response = "📁 *Категории компьютерных комплектующих:*\n\n"

        for category in categories:
            response += f"• {category['icon']} *{category['name']}*\n"
            response += f"  {category['description']}\n"
            response += f"  🛒 Товаров: {category['product_count']}\n\n"

        response += f"*Всего категорий: {len(categories)}*\n"
        response += "*Выберите категорию в Web App для просмотра товаров*"

        bot.send_message(chat_id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка отправки категорий: {e}")
        bot.send_message(chat_id, "❌ Ошибка получения категорий")


def send_products_by_category(chat_id, category_slug):
    """Отправка товаров по категории"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.name, p.price, p.brand, p.in_stock, p.rating, p.stock_quantity, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.slug = ? 
            ORDER BY p.rating DESC, p.popularity DESC
            LIMIT 15
        """, (category_slug,))

        products = cursor.fetchall()
        conn.close()

        if not products:
            bot.send_message(chat_id, f"❌ В категории '{category_slug}' не найдено товаров")
            return

        category_name = products[0]['category_name'] if products else category_slug

        response = f"🛒 *Товары категории {category_name}:*\n\n"

        for i, product in enumerate(products, 1):
            stock_status = "✅ В наличии" if product['in_stock'] else "⏳ Под заказ"
            stock_info = f" (осталось: {product['stock_quantity']})" if product['stock_quantity'] > 0 else ""

            rating_text = ""
            if product['rating'] and product['rating'] > 0:
                full_stars = int(product['rating'])
                half_star = product['rating'] - full_stars >= 0.5
                stars = "⭐" * full_stars
                if half_star:
                    stars += "½"
                rating_text = f" | {stars}"

            response += f"*{i}. {product['name']}*\n"
            response += f"   🏷️ {product['brand']}\n"
            response += f"   💰 {product['price']:,.0f}₽\n"
            response += f"   📊 {stock_status}{stock_info}{rating_text}\n\n"

        response += f"*Найдено товаров: {len(products)}*\n"
        response += "*Используйте поиск для нахождения конкретных товаров*"

        bot.send_message(chat_id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка отправки товаров по категории: {e}")
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")


def send_product_details(chat_id, product_id):
    """Отправка детальной информации о товаре"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name, p.description, p.price, p.brand, p.specs, p.rating, 
                   p.in_stock, p.stock_quantity, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        """, (product_id,))

        product = cursor.fetchone()
        conn.close()

        if not product:
            bot.send_message(chat_id, "❌ Товар не найден")
            return

        stock_status = "✅ В наличии" if product['in_stock'] else "⏳ Под заказ"
        stock_info = f"\n📦 *Остаток на складе:* {product['stock_quantity']} шт." if product[
                                                                                        'stock_quantity'] > 0 else ""

        rating = product['rating'] or 0
        stars = "⭐" * int(rating)
        if rating % 1 >= 0.5:
            stars += "½"

        response = f"""
🛒 *{product['name']}*

*Бренд:* {product['brand']}
*Категория:* {product['category_name']}
*Цена:* {product['price']:,.0f}₽
*Наличие:* {stock_status}{stock_info}
*Рейтинг:* {stars} ({rating}/5)

*Описание:*
{product['description']}

*Характеристики:*
{product['specs']}

*Для заказа используйте Web App интерфейс!*
        """

        bot.send_message(chat_id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка отправки деталей товара: {e}")
        bot.send_message(chat_id, "❌ Ошибка получения информации")


def search_products_web(chat_id, query):
    """Поиск товаров из Web App"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name, p.brand, p.price, p.in_stock, p.rating, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.name LIKE ? OR p.brand LIKE ? OR p.description LIKE ? OR c.name LIKE ?
            ORDER BY p.rating DESC, p.price
            LIMIT 15
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))

        products = cursor.fetchall()
        conn.close()

        if not products:
            bot.send_message(chat_id, f"❌ По запросу '{query}' ничего не найдено")
            return

        response = f"🔍 *Результаты поиска: '{query}'*\n\n"

        for i, product in enumerate(products, 1):
            stock_status = "✅" if product['in_stock'] else "⏳"

            rating_text = ""
            if product['rating'] and product['rating'] > 0:
                stars = "⭐" * int(product['rating'])
                if product['rating'] % 1 >= 0.5:
                    stars += "½"
                rating_text = f" | {stars}"

            response += f"*{i}. {product['name']}*\n"
            response += f"   🏷️ {product['brand']} | 📁 {product['category_name']}\n"
            response += f"   💰 {product['price']:,.0f}₽\n"
            response += f"   📊 {stock_status}{rating_text}\n\n"

        response += f"*Найдено товаров: {len(products)}*\n"
        response += "*Для уточнения используйте более конкретный запрос*"

        bot.send_message(chat_id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка поиска из Web App: {e}")
        bot.send_message(chat_id, "❌ Ошибка поиска")


def send_top_products(chat_id):
    """Отправка топа товаров"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name, p.brand, p.price, p.rating, p.popularity, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.rating > 0 
            ORDER BY p.rating DESC, p.popularity DESC 
            LIMIT 10
        """)

        products = cursor.fetchall()
        conn.close()

        if not products:
            bot.send_message(chat_id, "❌ Нет данных для топа")
            return

        response = "🏆 *Топ-10 товаров компьютерного магазина:*\n\n"

        for i, product in enumerate(products, 1):
            stars = "⭐" * int(product['rating'])
            if product['rating'] % 1 >= 0.5:
                stars += "½"

            response += f"*{i}. {product['name']}*\n"
            response += f"   🏷️ {product['brand']} | 📁 {product['category_name']}\n"
            response += f"   💰 {product['price']:,.0f}₽\n"
            response += f"   ⭐ {stars} | 👍 {product['popularity']}\n\n"

        response += "*Рейтинг основан на оценках покупателей*"

        bot.send_message(chat_id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка отправки топа: {e}")
        bot.send_message(chat_id, "❌ Ошибка получения топа")


def create_order_web(chat_id, user, order_data):
    """Создание заказа из Web App"""
    try:
        if not order_data or 'items' not in order_data or not order_data['items']:
            bot.send_message(chat_id, "❌ Корзина пуста!")
            return

        items = order_data['items']
        total_price = order_data.get('total', 0)
        address = order_data.get('address', 'Не указан')
        phone = order_data.get('phone', 'Не указан')
        notes = order_data.get('notes', '')

        # Создаем заказ в БД
        order_id = create_order(
            user.id,
            user.first_name,
            items,
            total_price,
            address,
            phone,
            notes
        )

        if order_id:
            # Формируем сообщение о заказе
            response = f"""
✅ *Заказ #{order_id} успешно оформлен!*

*Информация о заказе:*
👤 *Покупатель:* {user.first_name} (@{user.username or 'не указан'})
📱 *Телефон:* {phone}
🏠 *Адрес доставки:* {address}
📅 *Дата оформления:* {datetime.now().strftime('%d.%m.%Y %H:%M')}

*Состав заказа:*
"""

            for item in items:
                product_name = item.get('name', 'Неизвестный товар')
                quantity = item.get('quantity', 1)
                price = item.get('price', 0)
                response += f"• {product_name} x{quantity} = {price * quantity:,.0f}₽\n"

            response += f"\n💰 *Итого к оплате:* {total_price:,.0f}₽\n"
            response += "📊 *Статус:* Ожидает обработки\n\n"
            response += "📞 Наш менеджер свяжется с вами в течение 30 минут для подтверждения заказа."

            bot.send_message(chat_id, response, parse_mode='Markdown')

            # Уведомление для администратора (если нужно)
            # bot.send_message(ADMIN_CHAT_ID, f"Новый заказ #{order_id} от @{user.username}")

        else:
            bot.send_message(chat_id, "❌ Ошибка при создании заказа. Попробуйте еще раз.")

    except Exception as e:
        logger.error(f"Ошибка создания заказа из Web App: {e}")
        bot.send_message(chat_id, "❌ Ошибка оформления заказа. Попробуйте еще раз.")


def search_products(message):
    """Поиск товаров (традиционный)"""
    query = message.text.strip()
    user = message.from_user

    if not query:
        bot.send_message(message.chat.id, "❌ Введите запрос для поиска")
        return

    if len(query) < 2:
        bot.send_message(message.chat.id, "❌ Слишком короткий запрос (минимум 2 символа)")
        return

    update_user_activity(user.id, user.username, user.first_name, user.last_name)
    search_products_web(message.chat.id, query)


# ========== ОБРАБОТКА ТЕКСТОВЫХ КОМАНД ==========

@bot.message_handler(func=lambda message: True)
def handle_text_commands(message):
    """Обработка текстовых команд через кнопки"""

    if message.text == '📁 Категории':
        categories_command(message)

    elif message.text == '🔍 Поиск':
        search_command(message)

    elif message.text == '📊 Статистика':
        stats_command(message)

    elif message.text == '🆘 Помощь':
        help_command(message)

    elif message.text == '⭐ Топ товары':
        top_command(message)

    elif message.text == '📞 Контакты':
        bot.send_message(
            message.chat.id,
            "📞 *Контакты магазина компьютерных комплектующих:*\n\n"
            "*Адрес:* г. Москва, ул. Компьютерная, д. 15\n"
            "*Телефон:* +7 (999) 123-45-67\n"
            "*Email:* shop@computer-parts.ru\n"
            "*График работы:* Пн-Пт 10:00-20:00, Сб-Вс 11:00-18:00\n\n"
            "*Техническая поддержка бота:* @tech_support\n"
            "*Web App:* " + WEB_APP_URL
        )

    elif message.text.lower() in ['привет', 'hello', 'hi']:
        bot.send_message(
            message.chat.id,
            f"👋 Привет, {message.from_user.first_name}!\n"
            f"Добро пожаловать в магазин компьютерных комплектующих!\n"
            f"Используйте /start для доступа к функциям бота."
        )

    else:
        bot.send_message(
            message.chat.id,
            "🤔 Не понимаю команду. Используйте кнопки меню или команды:\n"
            "/start - главное меню\n"
            "/help - помощь\n"
            "/web - Web App интерфейс"
        )


# ========== ЗАПУСК БОТА ==========

if __name__ == '__main__':
    print("🚀 Инициализация бота компьютерных комплектующих...")

    # Инициализация базы данных
    if not os.path.exists(DB_PATH):
        print("📁 Создание новой базы данных...")
        init_database()
    else:
        print("📁 База данных уже существует, проверяем структуру...")

    # Проверка статистики
    stats = get_store_statistics()
    if stats:
        print(f"📊 Товаров в базе: {stats['total_products']}")
        print(f"📊 Категорий: {stats['total_categories']}")
        print(f"📊 Пользователей: {stats['total_users']}")

    print("=" * 60)
    print("✅ Бот запущен и готов к работе!")
    print("📱 Откройте Telegram и найдите бота")
    print("⚡ Используйте /start для начала работы")
    print("🛒 Используйте Web App для удобного заказа")
    print("ℹ️  Используйте Ctrl+C для остановки")
    print("=" * 60)

    try:
        bot.polling(none_stop=True, interval=0, timeout=30)
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")