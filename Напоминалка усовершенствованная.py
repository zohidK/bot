import telebot
from telebot import types
import schedule
import time
import threading
import json
import os

API_TOKEN = '7200421823:AAE65xznIJuB6wdQSNyCWxcDwliuk8xt5zA'
bot = telebot.TeleBot(API_TOKEN)


# Словарь для хранения расписания лекарств для каждого пользователя
medications = {}

# Загрузка данных из файла
if os.path.exists("medications.json"):
    with open("medications.json", "r", encoding="utf-8") as f:
        medications = json.load(f)


# Функция для отправки напоминания
def send_reminder(chat_id, medication):
    bot.send_message(chat_id, f"Время принимать: {medication}")


# Функция для планирования напоминаний
def schedule_reminders():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Функция для сохранения данных в файл
def save_data():
    with open("medications.json", "w", encoding="utf-8") as f:
        json.dump(medications, f)


# Команда /start
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=3)
    btn1 = types.KeyboardButton("Добавить лекарство")
    btn2 = types.KeyboardButton("Список лекарств")
    btn3 = types.KeyboardButton("Удалить лекарство")
    btn4 = types.KeyboardButton("Настройки напоминаний")
    btn5 = types.KeyboardButton("Редактировать лекарство")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите команду:", reply_markup=markup)


# Команда для добавления лекарства
@bot.message_handler(func=lambda message: message.text == "Добавить лекарство")
def set_schedule(message):
    msg = bot.send_message(message.chat.id, "Введите название лекарства и время (например, 'Аспирин 14:00 Пн'):")
    bot.register_next_step_handler(msg, process_schedule)


def process_schedule(message):
    try:
        med_info = message.text.split()
        medication = med_info[0]
        time_str = med_info[1]
        day = med_info[2].lower()

        # Проверка на корректность дня
        days_of_week = {'пн': 'mon', 'вт': 'tue', 'ср': 'wed', 'чт': 'thu', 'пт': 'fri', 'сб': 'sat', 'вс': 'sun'}
        if day not in days_of_week:
            bot.send_message(message.chat.id, "Ошибка! Укажите день недели (Пн, Вт, Ср, Чт, Пт, Сб, Вс).")
            return

        # Сохраняем лекарство
        if str(message.chat.id) not in medications:
            medications[str(message.chat.id)] = []

        medications[str(message.chat.id)].append((medication, time_str, day))
        save_data()

        # Запланируем напоминание
        schedule.every().day.at(time_str).do(send_reminder, message.chat.id, medication)

        bot.send_message(message.chat.id, f"Напоминание для {medication} установлено на {time_str} в {day}.")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка! Пожалуйста, введите корректные данные.")


# Команда для списка лекарств
@bot.message_handler(func=lambda message: message.text == "Список лекарств")
def list_medications(message):
    meds = medications.get(str(message.chat.id), [])
    if meds:
        response = "Ваше расписание:\n"
        for index, (med, time_str, day) in enumerate(meds):
            response += f"{index + 1}. {med} - {time_str} ({day.capitalize()})\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "У вас нет запланированных приемов.")


# Команда для удаления лекарства
@bot.message_handler(func=lambda message: message.text == "Удалить лекарство")
def delete_schedule(message):
    meds = medications.get(str(message.chat.id), [])
    if not meds:
        bot.send_message(message.chat.id, "У вас нет запланированных приемов.")
        return

    response = "Выберите лекарство для удаления:\n"
    for index, (med, time_str, day) in enumerate(meds):
        response += f"{index + 1}. {med} - {time_str} ({day.capitalize()})\n"

    msg = bot.send_message(message.chat.id, response)
    bot.register_next_step_handler(msg, process_delete)


def process_delete(message):
    try:
        index = int(message.text) - 1
        meds = medications.get(str(message.chat.id), [])
        if 0 <= index < len(meds):
            med_to_remove = meds[index]
            medications[str(message.chat.id)].pop(index)
            save_data()
            bot.send_message(message.chat.id, f"{med_to_remove[0]} успешно удалено из расписания.")
        else:
            bot.send_message(message.chat.id, "Ошибка! Неверный номер.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите номер лекарства.")


# Команда для редактирования лекарства
@bot.message_handler(func=lambda message: message.text == "Редактировать лекарство")
def edit_schedule(message):
    meds = medications.get(str(message.chat.id), [])
    if not meds:
        bot.send_message(message.chat.id, "У вас нет запланированных приемов.")
        return

    response = "Выберите лекарство для редактирования:\n"
    for index, (med, time_str, day) in enumerate(meds):
        response += f"{index + 1}. {med} - {time_str} ({day.capitalize()})\n"

    msg = bot.send_message(message.chat.id, response)
    bot.register_next_step_handler(msg, process_edit)


def process_edit(message):
    try:
        index = int(message.text) - 1
        meds = medications.get(str(message.chat.id), [])
        if 0 <= index < len(meds):
            med_to_edit = meds[index]
            msg = bot.send_message(message.chat.id,
                                   f"Введите новые данные для {med_to_edit[0]} (формат: 'Название Время День', например, 'Парацетамол 15:00 Вт'):")
            bot.register_next_step_handler(msg, update_schedule, index)
        else:
            bot.send_message(message.chat.id, "Ошибка! Неверный номер.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите номер лекарства.")


def update_schedule(message, index):
    try:
        med_info = message.text.split()
        medication = med_info[0]
        time_str = med_info[1]
        day = med_info[2].lower()

        # Проверка на корректность дня
        days_of_week = {'пн': 'mon', 'вт': 'tue', 'ср': 'wed', 'чт': 'thu', 'пт': 'fri', 'сб': 'sat', 'вс': 'sun'}
        if day not in days_of_week:
            bot.send_message(message.chat.id, "Ошибка! Укажите день недели (Пн, Вт, Ср, Чт, Пт, Сб, Вс).")
            return

        # Обновляем лекарство
        medications[str(message.chat.id)][index] = (medication, time_str, day)
        save_data()

        bot.send_message(message.chat.id, f"Лекарство обновлено: {medication} - {time_str} ({day.capitalize()}).")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка! Пожалуйста, введите корректные данные.")


# Команда для настройки напоминаний
@bot.message_handler(func=lambda message: message.text == "Настройки напоминаний")
def settings_reminders(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton("Ежедневно")
    btn2 = types.KeyboardButton("Каждые 2 дня")
    btn3 = types.KeyboardButton("Каждые 3 дня")
    btn_back = types.KeyboardButton("Назад")
    markup.add(btn1, btn2, btn3, btn_back)
    bot.send_message(message.chat.id, "Выберите частоту напоминаний:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ["Ежедневно", "Каждые 2 дня", "Каждые 3 дня"])
def set_reminder_frequency(message):
    frequency = message.text
    # Здесь можно добавить логику для изменения частоты напоминаний, если это требуется
    bot.send_message(message.chat.id, f"Частота напоминаний установлена на: {frequency}.")
    # Возврат в главное меню
    start_command(message)


@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    start_command(message)


# Запускаем поток для планирования
threading.Thread(target=schedule_reminders, daemon=True).start()

# Запускаем бота
bot.polling(none_stop=True)

