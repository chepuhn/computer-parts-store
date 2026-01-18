import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
DB_PATH = 'computer_parts.db'
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://chepuhn.github.io/computer-parts-store/')
BOT_NAME = "Computer Parts Store"
BOT_VERSION = "1.0.0"
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')