import time
import os
import requests
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from aiogram import Bot, types
import time
import os
import requests
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Создаем подключение к основной базе данных (users.db)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Создаем подключение к новой базе данных для отслеживания отправленных товаров (sent_items.db)
sent_items_conn = sqlite3.connect("sent_items.db")
sent_items_cursor = sent_items_conn.cursor()

# Функция для создания таблицы в базе данных sent_items.db
def create_sent_items_table():
    sent_items_cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_items (
        user_id INTEGER,
        title TEXT,
        price TEXT,
        PRIMARY KEY (user_id, title, price)
    )
    """)
    sent_items_conn.commit()

# Вызовем эту функцию при инициализации парсера
create_sent_items_table()

# Настройки для отключения SSL и WebRTC
chrome_options = Options()
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-extensions")

chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")

# Функция для получения ссылки на фильтр из основной базы данных
def get_tracking_url(user_id):
    cursor.execute("SELECT tracking_url FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None

# Флаг для контроля остановки парсера
is_parsing = False

# Функция для создания кнопки "Остановить парсер"
def get_stop_parsing_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton(text="Остановить парсер", callback_data="stop_parsing"))



# Функция для фильтрации отправленных товаров
def filter_item(user_id, item):
    # Проверяем, отправлялся ли уже товар с такой ценой и адресом
    sent_items_cursor.execute("SELECT * FROM sent_items WHERE user_id = ? AND title = ? AND price = ?", 
                              (user_id, item['title'], item['price']))
    result = sent_items_cursor.fetchone()

    if result:
        return False  # Если товар уже был отправлен, возвращаем False

    # Если товар новый, добавляем его в базу данных отправленных товаров
    sent_items_cursor.execute("INSERT INTO sent_items (user_id, title, price) VALUES (?, ?, ?)", 
                              (user_id, item['title'], item['price']))
    sent_items_conn.commit()

    return True  # Если товар новый, возвращаем True

# Перезапуск браузера и открытие страницы с ссылкой
def restart_browser(driver, user_id):
    try:
        link = get_tracking_url(user_id)
        if not link:
            print(f"Ссылка для фильтра не найдена для пользователя {user_id}")
            return driver

        driver.quit()  # Закрываем текущий браузер
        time.sleep(2)  # Небольшая задержка перед открытием нового окна

        # Запускаем новый браузер
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(link)  # Используем ссылку из базы данных

        print(f"Перезапустили браузер для пользователя {user_id} с ссылкой {link}")

        return driver
    except Exception as e:
        print(f"Ошибка при перезапуске браузера: {e}")
        return driver

# Асинхронная функция для парсинга
async def parse_avito_direct1(user_id, bot, chat_id):
    link = get_tracking_url(user_id)
    if not link:
        print("Ссылка для фильтра не найдена.")
        return []

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(link)  # Открываем страницу с ссылкой из базы данных

    try:
        while True:
            time.sleep(10)
            try:
                first_item = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.iva-item-root-Se7z4'))
                )
                
                # Прокручиваем страницу, чтобы элемент стал видимым
                driver.execute_script("arguments[0].scrollIntoView(true);", first_item)
                time.sleep(1)  # Даем время на прокрутку

                # Попытка кликнуть по товару
                ActionChains(driver).move_to_element(first_item).click().perform()
                print("Перешли на страницу первого товара.")

                time.sleep(5)

                # Ожидаем и собираем данные о товаре
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                title_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h3[itemprop="name"]'))
                )
                title = title_element.text
                print(f"Название товара: {title}")

                link_element = driver.find_element(By.CSS_SELECTOR, 'a[itemprop="url"]')
                link = link_element.get_attribute('href')
                print(f"Ссылка на товар: {link}")

                price_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span.price-root-IfnJI meta[itemprop="price"]'))
                )
                price = price_element.get_attribute('content')
                print(f"Цена товара: {price} руб.")

                address_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.geo-root-NrkbV .styles-module-noAccent-XIvJm[title]'))
                )
                address = address_element.text
                print(f"Адрес товара: {address}")

                rating_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.SellerRating-scoreAndStars-_ti2Y .buyer-location-1y4c9y0'))
                )
                rating = rating_element.text
                print(f"Рейтинг товара: {rating}")

                img_elements = driver.find_elements(By.CSS_SELECTOR, 'img.photo-slider-image-xjG6U')
                if not os.path.exists('images'):
                    os.makedirs('images')
                for index, img_element in enumerate(img_elements[:3]):
                    img_url = img_element.get_attribute('src')
                    img_name = f"images/photo_{index+1}.jpg"
                    img_data = requests.get(img_url).content
                    with open(img_name, 'wb') as img_file:
                        img_file.write(img_data)
                    print(f"Сохранено изображение: {img_name}")
                
                # Формируем товар
                item = {
                    "title": title,
                    "price": price,
                    "address": address,
                    "link": link,
                    "image": img_elements[0].get_attribute('src') if img_elements else None,
                    "rating": rating
                }

                # Применяем фильтрацию
                if filter_item(user_id, item):
                    # Отправка нового объявления
                    text = f"<b>{title}</b>\n" \
                           f"Цена: {price} руб.\n" \
                           f"Адрес: {address}\n" \
                           f"<a href='{link}'>Ссылка на товар</a>"
                    
                    if img_elements:
                        await bot.send_photo(chat_id, photo=img_elements[0].get_attribute('src'), caption=text, parse_mode="HTML")
                    else:
                        await bot.send_message(chat_id, text, parse_mode="HTML")
                    time.sleep(2)
                
                driver.back()

            except Exception as e:
                print(f"Ошибка: {e}")

            driver = restart_browser(driver, user_id)  # Перезапуск браузера

    except Exception as e:
        print(f"Ошибка в процессе парсинга: {e}")
