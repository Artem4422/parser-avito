import logging
import asyncio
import requests




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

# Создаем подключение к базе данных
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Обновляем таблицу для хранения фильтра отслеживания и времени последней проверки
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    subscription_active BOOLEAN DEFAULT FALSE,
    tracking_filter TEXT,
    last_check DATETIME
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
            [InlineKeyboardButton(text="Основной поиск", callback_data="main_search")],
            [InlineKeyboardButton(text="Начать отслеживать", callback_data="start_tracking")],
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






import asyncio
import re
from datetime import datetime
import logging
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import types

# Логирование для отладки
logging.basicConfig(level=logging.DEBUG)

# Глобальные переменные для хранения фильтров и времени последней проверки
user_filters = {}
user_last_check = {}

# Состояния для FSM
class UserState(StatesGroup):
    awaiting_filter_tracking = State()  # Ожидание ссылки на фильтр для отслеживания


# Обработка кнопки "Начать отслеживать"
@dp.callback_query(lambda c: c.data == "start_tracking")
async def start_tracking(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await call.message.answer("Пожалуйста, отправьте ссылку на фильтр для отслеживания новых объявлений.")
    
    # Устанавливаем состояние ожидания фильтра для отслеживания
    await state.set_state(UserState.awaiting_filter_tracking)
    logging.info(f"Пользователь {user_id} перешел в состояние ожидания фильтра.")

import asyncio
from datetime import datetime, timedelta
import logging
from aiogram import types
import pytz

from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext

from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
# Логирование для отладки
logging.basicConfig(level=logging.DEBUG)
# Глобальные переменные для хранения времени следующей проверки
user_next_check = {}



# Обработка ссылки на фильтр (для отслеживания)
@dp.message(StateFilter(UserState.awaiting_filter_tracking))  # Используем фильтр состояний
async def handle_tracking_link(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    link = message.text.strip()

    logging.info(f"Пользователь {user_id} отправил ссылку для отслеживания: {link}")

    if "avito.ru" not in link:
        await message.answer("Пожалуйста, отправьте корректную ссылку с сайта Авито.")
        logging.info(f"Пользователь {user_id} отправил некорректную ссылку для отслеживания.")
        return

    # Сохраняем ссылку для отслеживания
    user_filters[user_id] = link
    user_sent_items[user_id] = []  # Список для хранения отправленных объявлений
    user_last_check[user_id] = datetime.now()
    
    # Устанавливаем время первой проверки на 00:00
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    next_check_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now > next_check_time:
        next_check_time += timedelta(days=1)  # Если текущее время уже после 00:00, проверяем завтра

    # Устанавливаем время следующей проверки
    user_next_check[user_id] = next_check_time

    # Информируем пользователя, что отслеживание активировано
    await message.answer("Отслеживание фильтра активировано. Будут приходить новые объявления каждую ночь с 00:00.")
    logging.info(f"Отслеживание для пользователя {user_id} активировано.")

    # Запускаем задачу отслеживания
    asyncio.create_task(track_new_ads(user_id))

    # Завершаем состояние
    await state.clear()

# Глобальные переменные для хранения уже отправленных объявлений
user_sent_items = {}

import asyncio
import pytz
from datetime import datetime, timedelta
import logging

# Настроим локальную временную зону для работы с временем
timezone = pytz.timezone('Europe/Moscow')  # Установите нужную временную зону

async def track_new_ads(user_id):
    seen_items = set()  # Множество для хранения просмотренных объявлений (по комбинации заголовка, цены и ссылки)

    while user_id in user_filters:
        current_time = datetime.now(timezone)
        # Находим ближайшее время для начала отслеживания (кратное 2 минутам)
        if current_time.minute % 2 != 0:
            # Если время не кратно 2 минутам, находим следующее время
            start_time = current_time.replace(second=0, microsecond=0) + timedelta(minutes=(2 - current_time.minute % 2))
        else:
            start_time = current_time.replace(second=0, microsecond=0)

        # Ждем до следующего времени
        wait_time = (start_time - current_time).total_seconds()
        logging.info(f"Бот начнёт проверку в {start_time.strftime('%H:%M:%S')}, осталось {wait_time} секунд.")
        await asyncio.sleep(wait_time)

        while user_id in user_filters:
            link = user_filters[user_id]
            logging.info(f"Пользователь {user_id} начнёт проверку для {link}. Следующая проверка через 2 минуты.")

            # Парсим объявления по ссылке
            items = parse_avito_direct(link)

            # Фильтруем объявления по названию и цене, пропускаем повторяющиеся
            new_items = []
            for item in items:
                if (item["title"], item["price"], item["link"]) not in seen_items:
                    new_items.append(item)
                    seen_items.add((item["title"], item["price"], item["link"]))

            if new_items:
                # Отправляем новые объявления
                for item in new_items[:1]:
                    text = f"📰 Новое объявление:\n\n"
                    text += f"🔹 Заголовок: {item['title']}\n"
                    text += f"💸 Цена: {item['price']}\n"
                    text += f"🔗 Ссылка: {item['link']}\n"
                    if item['image']:
                        await bot.send_photo(user_id, item['image'], caption=text)
                    else:
                        await bot.send_message(user_id, text)

            # Обновляем время последней проверки
            user_last_check[user_id] = datetime.now()

            # Пауза до следующей проверки (2 минуты)
            await asyncio.sleep(120)  # Проверка каждые 2 минуты





# Обработка обычного поиска
@dp.message()
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    link = message.text.strip()

    # Проверяем, не находимся ли мы в состоянии отслеживания
    if user_id in user_filters:
        await message.answer("Вы уже активировали отслеживание. Сначала остановите его /stop_tracking .")
        return

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


@dp.callback_query(lambda c: c.data == "stop_tracking")
async def stop_tracking(call: types.CallbackQuery):
    user_id = call.from_user.id

    # Останавливаем отслеживание
    if user_id in user_filters:
        del user_filters[user_id]
        del user_last_check[user_id]
        await call.message.answer("Отслеживание объявлений прекращено.")
    else:
        await call.message.answer("Вы не активировали отслеживание.")











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






# Запуск бота
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

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
