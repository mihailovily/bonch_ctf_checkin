import os
from telebot import types
import telebot
import sqlite3
import random
from datetime import datetime


# инит
token = open("tokens/telegram.txt").readline()
admin = open("tokens/admin.txt").readline()
bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start", "help"])  # старт
def send_welcome(message):
    usr_id = str(message.from_user.id)  # userid
    keyboard = types.ReplyKeyboardMarkup(True)  # генерируем клаву
    butt_check = types.KeyboardButton(text="Отметиться")
    butt_visits = types.KeyboardButton(text="Мои посещения")
    butt_admin = types.KeyboardButton(text="Админство")
    if usr_id == admin:
        keyboard.add(butt_check, butt_visits, butt_admin)
    else:
        keyboard.add(butt_check, butt_visits)
    bot.reply_to(
        message, "Привет, " + str(message.from_user.first_name), reply_markup=keyboard
    )  # здороваемся
    bot.reply_to(
        message,
        "Добро пожаловать на собрание клуба b0nch_CTF. Отметься, нам очень важно видеть статистику посещаемости. Автор этого творения: @mihailovily",
    )


@bot.message_handler(commands=["check"])
@bot.message_handler(regexp="Отметиться")
def recieve_checkin(message):
    bot.reply_to(message, "Отправь код отметки")
    bot.register_next_step_handler(message, check_code)
    # кушаем ответ, пихаем в след функцию


# проверка на наличие кода в базе
def check_code(message):
    connection = sqlite3.connect("my_database.db")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT is_active FROM ActiveCheckins WHERE code IS '{code}'".format(
            code=message.text
        )
    )
    result = cursor.fetchall()
    bot.reply_to(message, "Проверка кода...")
    if result != []:
        if result[0][0] == 1:
            bot.reply_to(message, "Отлично, секунду...")
            checkin_user(message)  # если код правильный, то чекиним пользователя
        else:
            bot.reply_to(message, "Занятие завершено")
    else:
        bot.reply_to(message, "Код отметки не подходит")


def checkin_user(message):
    connection = sqlite3.connect("my_database.db")
    cursor = connection.cursor()
    usr_id = message.from_user.id
    usr_username = message.from_user.username
    # глобальная отметка
    cursor.execute(
        "SELECT * FROM Users WHERE tgid IS '{tgid}'".format(tgid=str(usr_id))
    )
    users = cursor.fetchall()
    if users == []:
        # print("nouser globally")
        cursor.execute(
            "INSERT INTO Users (tgid, username, name, visits) VALUES (?, ?, ?, ?)",
            (str(usr_id), str(usr_username), str(message.from_user.first_name), 1),
        )
    else:
        # print("exists")
        cursor.execute(
            "SELECT visits FROM Users WHERE tgid IS '{tgid}'".format(tgid=str(usr_id))
        )
        user_visits = int(cursor.fetchall()[0][0])
        cursor.execute(
            "UPDATE Users SET visits = ? WHERE tgid = ?", (user_visits + 1, str(usr_id))
        )
    # локальная отметка
    # сопоставляем код и таблицу
    cursor.execute(
        "SELECT data FROM ActiveCheckins WHERE code IS '{tgid}'".format(
            tgid=str(message.text)
        )
    )
    local_table_name = cursor.fetchall()[0][0]

    cursor.execute(
        "SELECT * FROM '{table}' WHERE tgid IS '{tgid}'".format(
            tgid=str(usr_id), table=str(local_table_name)
        )
    )
    users = cursor.fetchall()
    if users == []:
        # print("nouser locally")
        cursor.execute(
            "INSERT INTO '{table}' (tgid, username, name) VALUES ('{tgid}', '{username}', '{name}')".format(
                table=str(local_table_name),
                tgid=str(usr_id),
                username=str(usr_username),
                name=str(message.from_user.first_name),
            )
        )

    connection.commit()
    connection.close()
    bot.reply_to(message, "Отлично, записал на занятие")


def is_user_exists(tgid, dbname):
    pass


@bot.message_handler(commands=["visits"])
@bot.message_handler(regexp="Мои посещения")
def my_visits(message):
    connection = sqlite3.connect("my_database.db")
    cursor = connection.cursor()
    usr_id = message.from_user.id
    cursor.execute(
        "SELECT visits FROM Users WHERE tgid IS '{tgid}'".format(tgid=str(usr_id))
    )
    bot.reply_to(
        message,
        "Количество твоих посещений: {visits}".format(visits=cursor.fetchall()[0][0]),
    )


@bot.message_handler(commands=["admin"])
@bot.message_handler(regexp="Админство")
def admin_check(message):
    usr_id = str(message.from_user.id)
    if usr_id == admin:
        bot.reply_to(
            message, "Что делаем дальше?\n1. Начать новое занятие\n2. Завершить занятие"
        )

        bot.register_next_step_handler(message, admin_razvilka)


def admin_razvilka(message):
    if message.text == "1":
        bot.reply_to(message, "Подтверди намерения")
        bot.register_next_step_handler(message, start_check)
    elif message.text == "2":
        connection = sqlite3.connect("my_database.db")
        cursor = connection.cursor()
        cursor.execute("SELECT code FROM ActiveCheckins WHERE is_active IS 1")
        to_answer = "Занятие с каким кодом необходимо завершить?\n" + str(
            cursor.fetchall()
        )
        bot.reply_to(message, to_answer)
        bot.register_next_step_handler(message, finish_check)


def start_check(message):
    if str(message.text) in "Yy":
        date_check = datetime.today().strftime("%d.%m.%Y")
        code_check = gen_auth_code()
        usr_id = str(message.from_user.id)
        connection = sqlite3.connect("my_database.db")
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM ActiveCheckins WHERE code IS '{codd}'".format(
                codd=str(code_check)
            )
        )
        if cursor.fetchall() == []:
            cursor.execute(
                "INSERT INTO ActiveCheckins (data, code, is_active) VALUES (?, ?, ?)",
                (str(date_check), str(code_check), 1),
            )
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS '{table}' (id INTEGER PRIMARY KEY, tgid TEXT, username TEXT, name TEXT)""".format(
                    table=str(date_check)
                )
            )
            bot.send_message(
                usr_id, "Успешно, код отметки {otmetka}".format(otmetka=code_check)
            )
        else:
            bot.send_message(usr_id, "Занято")
        connection.commit()
        connection.close()


def gen_auth_code():
    s = ""
    for i in range(5):
        s += random.choice("QWERTYUIPASDFGHJKLZXCVBNM123456789")
    return s


def finish_check(message):
    code_check = message.text
    usr_id = str(message.from_user.id)
    connection = sqlite3.connect("my_database.db")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM ActiveCheckins WHERE code IS '{codd}'".format(
            codd=str(code_check)
        )
    )
    if cursor.fetchall() != []:
        cursor.execute(
            "UPDATE ActiveCheckins SET is_active = ? WHERE code = ?",
            (0, str(code_check)),
        )
        cursor.execute(
            "SELECT data FROM ActiveCheckins WHERE code IS '{tgid}'".format(
                tgid=str(code_check)
            )
        )
        local_table_name = cursor.fetchall()[0][0]
        cursor.execute(
            "SELECT * FROM '{tablitsa}'".format(tablitsa=str(local_table_name))
        )
        users_finally = cursor.fetchall()
        otchet = ""
        for k in users_finally:
            otchet += "{n}. id: {id}, username: {username}, name: {name}\n".format(
                n=k[0], id=k[1], username=k[2], name=k[3]
            )
        bot.send_message(
            usr_id,
            "Занятие {date} с кодом {code} успешно завершено. Всего отметившихся: {visited}".format(
                date=str(local_table_name),
                code=code_check,
                visited=str(len(users_finally)),
            ),
        )
        bot.send_message(usr_id, otchet)
    else:
        bot.send_message(usr_id, "Такого не найдено")
    connection.commit()
    connection.close()


# если сообщение не распознано
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Я тебя немного не понял. Давай еще раз")


bot.infinity_polling()
