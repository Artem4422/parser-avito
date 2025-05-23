import logging
import asyncio
import requests

from parser import parse_avito_direct1  # Импортируем функцию парсинга


from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import time
import re
from datetime import datetime, timedelta
import logging
import requests
from bs4 import BeautifulSoup
import random
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import sqlite3

import sqlite3

# Создаем подключение к старой базе данных (обычной)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Обновляем таблицу для хранения фильтра отслеживания, времени последней проверки и ссылки
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    subscription_active BOOLEAN DEFAULT FALSE,
    tracking_filter TEXT,
    tracking_url TEXT,  -- Ссылка для отслеживания
    state TEXT,  -- Состояние отслеживания
    last_check DATETIME  -- Время последней проверки
)
""")
conn.commit()







conn.commit()

def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def set_subscription(user_id, active):
    cursor.execute("UPDATE users SET subscription_active = ? WHERE user_id = ?", (active, user_id))
    conn.commit()
    logging.info(f"Subscription for user {user_id} set to {active}")


def get_subscription(user_id):
    cursor.execute("SELECT subscription_active FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else False

# Функция парсинга, выполняющаяся в отдельной задаче
async def parse_user(user_id):
    print(f"Начинаем парсинг для пользователя {user_id}")
    await asyncio.sleep(5)  # Замените на реальный код парсинга
    print(f"Парсинг завершен для пользователя {user_id}")


API_TOKEN = "8084563968:AAGe7c9M_oscVQR6Cd_3yEmNJsa7yWpPcD8"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Словарь для хранения данных пользователей
user_data = {}

# Функция парсинга Авито

# Функция парсинга
def parse_avito_direct(url):
    try:
        headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        logging.info(f"Статус ответа: {response.status_code}, Длина ответа: {len(response.text)}")

        soup = BeautifulSoup(response.text, "lxml")
        items = []

        ads = soup.find_all("div", class_="iva-item-content-OWwoq")  # Класс объявления
        logging.info(f"Найдено {len(ads)} блоков с объявлениями.")

        # Ограничиваем количество найденных объявлений до 3
        ads = ads[:3]

        for ad in ads:
            # Заголовок
            title_tag = ad.find("h3")
            title = title_tag.text.strip() if title_tag else "Без названия"

            # Цена
            price_tag = ad.find("strong", class_="styles-module-root-LEIrw")
            price_span = price_tag.find("span") if price_tag else None
            price = price_span.text.strip() if price_span else "Цена не указана"

            # Ссылка
            link_tag = ad.find("a", href=True)
            link = "https://www.avito.ru" + link_tag['href'] if link_tag else "Ссылка отсутствует"

            # Изображение
            image_tag = ad.find("img")
            image = image_tag['src'] if image_tag else None

            # Дополнительные данные из страницы объявления
            seller_name = "Имя продавца не указано"
            seller_rating = "Рейтинг не указан"
            seller_reviews = "Отзывы не указаны"
            time_published = "Время публикации не указано"

            if link != "Ссылка отсутствует":
                try:
                    item_response = requests.get(link, headers=headers)
                    item_response.raise_for_status()
                    item_soup = BeautifulSoup(item_response.text, "lxml")

                    # Имя продавца
                    seller_name_tag = item_soup.find("div", class_="styles-module-root-Zabz6 styles-module-margin-top_none-_c4I_ styles-module-margin-bottom_none-QChmM styles-module-direction_vertical-_gIBq")
                    seller_name = seller_name_tag.text.strip() if seller_name_tag else "Имя продавца не указано"

                    # Рейтинг продавца
                    rating_tag = item_soup.find("span", class_="styles-module-theme-_4Zlk styles-module-theme-kvanA")
                    seller_rating = rating_tag.text.strip() if rating_tag else "Рейтинг не указан"

                    # Отзывы продавца
                    reviews_tag = item_soup.find("span", class_=["sstyles-module-root-o3j6a styles-module-size_m-n6S6Y styles-module-size_m-HtjNQ stylesMarningNormal-module-root-_BXZU stylesMarningNormal-module-paragraph-m-pH9s3"])
                    seller_reviews = reviews_tag.text.strip() if reviews_tag else "Отзывы не указаны"

                    # Время публикации
                    time_tag = item_soup.find("div", class_="style-seller-info-name-uWwYv js-seller-info-name")
                    time_published = time_tag.text.strip() if time_tag else "Время публикации не указано"
                except Exception as e:
                    logging.error(f"Ошибка парсинга страницы объявления: {e}")

            logging.info(f"Объявление: {title}, Цена: {price}, Продавец: {seller_name}, Рейтинг: {seller_rating}, Отзывы: {seller_reviews}, Время публикации: {time_published}, Ссылка: {link}")

            items.append({
                "title": title,
                "price": price,
                "link": link,
                "image": image,
                "time_published": time_published,
                "seller_name": seller_name,
                "seller_rating": seller_rating,
                "seller_reviews": seller_reviews,
            })

        logging.info(f"Найдено {len(items)} объявлений.")
        return items

    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return []






@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    
    # Добавляем нового пользователя в базу данных, если его нет
    add_user(user_id, message.from_user.username)
    
    # Получаем статус подписки из базы данных
    subscription_active = get_subscription(user_id)
    
    # Добавляем или обновляем информацию о подписке в словарь
    user_data[user_id] = {"subscription_active": subscription_active}
    
    # Определяем статус подписки
    subscription_status = "Активна" if subscription_active else "Не активна"
    # Получаем всех пользователей из базы данных
    cursor.execute("SELECT user_id FROM users WHERE tracking_filter IS NOT NULL AND subscription_active = TRUE")
    users = cursor.fetchall()

    # Создаем текст сообщения с информацией о подписке
    text = (
        "ℹ️ Личный кабинет\n\n"
        f"🔑 ID Кабинета: {message.from_user.id}\n"
        f"👤 Пользователь: {message.from_user.username or 'Не указан'}\n"
        "🔗 Ваша реферальная ссылка:\n"
        f"https://t.me/scanurik_bot?start={message.from_user.id}\n"
        f"🗂 Подписка на поиск: {subscription_status}\n"  # Добавляем статус подписки
    )

    # Тестовое изображение
    photo_url = "https://via.placeholder.com/500"

    # Создаем кнопки
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать отслеживать", callback_data="main_search")],
            [InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")]
        ]
    )

    # Отправляем сообщение с фото и кнопками
    await bot.send_photo(chat_id=message.chat.id, photo=photo_url, caption=text, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "main_search")
async def main_search(call: types.CallbackQuery):
    user_id = call.from_user.id

    # Проверка подписки в словаре
    subscription_active = user_data.get(user_id, {}).get("subscription_active", False)
    if not subscription_active:
        # Если подписка не активирована в словаре, проверяем в базе данных
        subscription_active = get_subscription(user_id)

    if not subscription_active:
        await call.message.answer("Основной поиск доступен только с активной подпиской.")
        return

    # Запрос на ссылку для поиска
    await call.message.answer("Отправьте ссылку на фильтр для поиска.")

    # Обновляем состояние пользователя, чтобы ожидать фильтр
    user_data[user_id] = {"state": "awaiting_filter"}




    
### Место для отслеживания обьявлений 


# Словарь для хранения отправленных товаров (ключ: user_id, значение: список отправленных товаров)
sent_items = {}

# Функция для выполнения запросов
def execute_query(query, params=()):
    try:
        cursor.execute(query, params)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")

# Обработчик команды /start, который запрашивает ссылку на фильтр
@dp.callback_query(lambda c: c.data == "start_tracking")
async def start_tracking(call: types.CallbackQuery):
    user_id = call.from_user.id

    # Проверяем, не активировано ли отслеживание для этого пользователя
    cursor.execute("SELECT state FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result and result[0] == 'tracking':
        await call.message.answer("Вы уже начали отслеживание. Подождите, пока оно завершится.")
        return

    # Запрашиваем ссылку на фильтр
    await call.message.answer("Пожалуйста, отправьте ссылку на фильтр Авито для отслеживания.")
    
    # Обновляем состояние пользователя, чтобы ожидать ссылку
    cursor.execute("REPLACE INTO users (user_id, state) VALUES (?, ?)", (user_id, "awaiting_tracking_url"))
    conn.commit()


def filter_item(user_id, item):
    # Проверяем, отправлялся ли уже товар с такой ценой и адресом
    if user_id in sent_items:
        for sent_item in sent_items[user_id]:
            if sent_item['price'] == item['price'] and sent_item['address'] == item['address']:
                return False  # Если товар уже был отправлен, возвращаем False
    else:
        # Если для пользователя ещё нет отправленных товаров, инициализируем список
        sent_items[user_id] = []

    # Добавляем товар в список отправленных
    sent_items[user_id].append(item)
    return True  # Если товар новый, возвращаем True


# Обработчик для получения ссылки на фильтр и начала отслеживания
@dp.message(lambda message: "avito.ru" in message.text)
async def handle_link_trac(message: types.Message):
    user_id = message.from_user.id
    link = message.text.strip()

    # Проверка на корректность ссылки
    if "avito.ru" not in link:
        await message.answer("Пожалуйста, отправьте корректную ссылку с сайта Авито.")
        return

    # Сохраняем ссылку в базе данных
    cursor.execute("UPDATE users SET tracking_url = ?, state = ? WHERE user_id = ?", (link, 'tracking', user_id))
    conn.commit()

    await message.answer(f"Ссылка для отслеживания успешно добавлена: {link}")

    # Получаем товары из парсера
    items = await parse_avito_direct1(user_id, bot, message.chat.id)  # Передаем user_id, bot, chat_id

    if not items:
        await message.answer("Не удалось найти объявления по указанной ссылке.")
        return

    # Сохраняем информацию о найденных товарах
    cursor.execute("UPDATE users SET state = ? WHERE user_id = ?", ('waiting_for_next_item', user_id))
    conn.commit()

    # Теперь нужно отправить объявление, пропуская те, которые уже отправлялись
    for item in items:
        if not filter_item(user_id, item):
            # Если товар уже был отправлен, пропускаем его
            print(f"Пропуск товара: {item['title']} (Цена: {item['price']}, Адрес: {item['address']})")
            continue  # Переходим к следующему товару
        else:
            # Отправляем товар
            await send_item_trac(user_id, message.chat.id)
            break  # После отправки первого подходящего объявления выходим из цикла


# Функция отправки объявления с фильтрацией
async def send_item_trac(user_id, chat_id):
    user = user_data.get(user_id)
    if not user or "items" not in user:
        await bot.send_message(chat_id, "Нет доступных объявлений для отображения.")
        return

    items = user["items"]
    index = user["current_index"]

    if index < 0 or index >= len(items):
        await bot.send_message(chat_id, "Вы достигли конца списка.")
        return

    item = items[index]

    # Формируем текст сообщения
    text = f"<b>{item['title']}</b>\n" \
           f"Цена: {item['price']} руб.\n" \
           f"Адрес: {item['address']}\n" \
           f"<a href='{item['link']}'>Ссылка на товар</a>"

    # Печатаем информацию о товаре для отладки
    print(f"Отправка объявления: {item['title']} - {item['price']} руб.")

    # Отправляем фото или текст
    if item['image']:
        await bot.send_photo(chat_id, photo=item['image'], caption=text, parse_mode="HTML")
    else:
        await bot.send_message(chat_id, text, parse_mode="HTML")

    # Обновляем индекс текущего товара
    user_data[user_id]["current_index"] += 1

    # Проверяем, если нужно продолжить парсить
    if user_data[user_id]["current_index"] < len(items):
        await send_item_trac(user_id, chat_id)  # Отправляем следующее объявление


##

# Обработка обычного поиска
@dp.message()
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    link = message.text.strip()

    

    # Удаляем символы, не относящиеся к ASCII
    link = re.sub(r"[^\x00-\x7F]+", "", link)  # Удаляет символы за пределами ASCII

    if "avito.ru" not in link:
        await message.answer("Пожалуйста, отправьте корректную ссылку с сайта Авито.")
        return

    # Основной поиск
    if user_data.get(user_id, {}).get("state") == "awaiting_filter":
        await message.answer("Ищу объявления, это может занять некоторое время...")

        items = parse_avito_direct(link)
        
        if not items:
            await message.answer("Не удалось найти объявления по указанной ссылке.")
            return

        # Сохраняем данные пользователя
        user_data[user_id] = {"items": items, "current_index": 0}
        
        # Отправляем первое объявление
        await send_item(user_id, message.chat.id)
        
        # Сбрасываем состояние пользователя после завершения
        user_data[user_id]["state"] = None













###
@dp.callback_query(lambda c: c.data == "buy_subscription")
async def buy_subscription(call: types.CallbackQuery):
    text = (
        "Для оформления подписки переведите 100р на карту:\n"
        "💳 Номер карты: 1234 5678 9012 3456\n\n"
        "После оплаты нажмите кнопку 'Оплатить'."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Потвердить", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )

    await bot.send_message(chat_id=call.from_user.id, text=text, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "confirm_payment")
async def confirm_payment(call: types.CallbackQuery):
    admin_id = "7830802188"  # Укажите ID администратора
    user_id = call.from_user.id

    # Уведомление администратору о запросе на подтверждение
    text = f"Пользователь {user_id} отправил запрос на подтверждение оплаты."
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data=f"approve_{user_id}")],
            [InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}")]
        ]
    )
    await bot.send_message(admin_id, text, reply_markup=keyboard)
    await call.message.answer("Запрос на подтверждение оплаты отправлен администратору.")


@dp.callback_query(lambda c: c.data.startswith("approve_"))
async def approve_subscription(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])

    # Обновляем подписку в базе данных
    set_subscription(user_id, True)

    # Обновляем подписку в словаре
    user_data[user_id]["subscription_active"] = True

    # Отправляем подтверждение пользователю
    await call.message.edit_text("Подписка успешно активирована!")
    await call.answer("Подписка подтверждена", show_alert=True)




@dp.callback_query(lambda call: call.data.startswith("decline_"))
async def decline_subscription(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(user_id, "Оплата не подтверждена. Пожалуйста, попробуйте снова.")
    await call.message.answer("Оплата отклонена.")

@dp.callback_query(lambda call: call.data.startswith("approve_"))
async def approve_subscription(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])  # Извлекаем user_id
    subscription_active = get_subscription(user_id)
    
    if subscription_active:
        await call.answer("Подписка активирована.")
    else:
        await call.answer("Подписка не активирована. Чтобы активировать подписку, используйте кнопку 'Купить подписку'.")

@dp.callback_query(lambda c: c.data.startswith("decline_"))
async def decline_subscription(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(user_id, "Оплата не подтверждена. Пожалуйста, попробуйте снова.")
    await call.message.answer("Оплата отклонена.")



async def send_item(user_id, chat_id):
    user = user_data.get(user_id)
    if not user or "items" not in user:
        await bot.send_message(chat_id, "Нет доступных объявлений для отображения.")
        return

    items = user["items"]
    index = user["current_index"]

    if index < 0 or index >= len(items):
        await bot.send_message(chat_id, "Вы достигли конца списка.")
        return

    item = items[index]

    # Создаем кнопки навигации
    buttons = []
    if index > 0:
        buttons.append([InlineKeyboardButton(text="Предыдущее", callback_data="prev")])
    if index < len(items) - 1:
        buttons.append([InlineKeyboardButton(text="Следующее", callback_data="next")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

# Формируем текст сообщения
    text = f"<b>{item['title']}</b>\n" \
       f"Цена: {item['price']}\n" \
       f"🕙 {item['seller_name']} (если пишет спросите - продавец скрыл)\n" \
       f"Рейтинг: {item['seller_rating']}\n" \
       f"Отзывы: {item['seller_reviews']}\n" \
       f"Время публикации: {item['time_published']}\n" \
       f"<a href='{item['link']}'>Ссылка на объявление</a>"

    # Отправляем фото или текст
    if item['image']:
        await bot.send_photo(chat_id, photo=item['image'], caption=text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)



# Хендлер кнопок навигации
@dp.callback_query()
async def handle_navigation(call: types.CallbackQuery):
    user = user_data.get(call.from_user.id)
    if not user:
        await call.answer("Данные не найдены. Отправьте ссылку заново.", show_alert=True)
        return

    if call.data == "prev":
        user["current_index"] -= 1
    elif call.data == "next":
        user["current_index"] += 1

    # Отправляем следующее или предыдущее объявление
    await send_item(call.from_user.id, call.message.chat.id)
    await call.answer()






import asyncio

async def track_announcements():
    while True:
        # Логика для отслеживания объявлений
        print("Проверка объявлений...")
        await asyncio.sleep(600)  # Пауза между проверками (10 минут)

async def main():
    dp.message.register(start_command, Command("start"))
    dp.message.register(handle_link)
    dp.callback_query.register(handle_navigation)

    # Получаем всех пользователей из базы данных
    cursor.execute("SELECT user_id FROM users WHERE tracking_filter IS NOT NULL AND subscription_active = TRUE")
    users = cursor.fetchall()

    # Запуск отслеживания объявлений для каждого пользователя
    for user in users:
        user_id = user[0]

    # Создаем задачу для отслеживания объявлений
    loop = asyncio.get_event_loop()
    loop.create_task(track_announcements())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())  # Запускаем главный цикл
