import os
from telebot import types
import telebot
import sqlite3


token = open("tokens/telegram.txt").readline()
admin = open("tokens/admin.txt").readline()
bot = telebot.TeleBot(token)  # инит


@bot.message_handler(commands=["start", "help"])  # старт
def send_welcome(message):
    usr_id = str(message.from_user.id)  # userid
    usr_name = str(message.from_user.first_name)  # имя юзера
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


def check_code(message):
    connection = sqlite3.connect("my_database.db")
    cursor = connection.cursor()
    flag = message.text
    cursor.execute(
        "SELECT is_active FROM ActiveCheckins WHERE code IS '{code}'".format(code=flag)
    )
    result = cursor.fetchall()
    print(result[0][0])
    bot.reply_to(message, "Проверка кода...")
    if result != []:
        if result[0][0] == 1:
            bot.reply_to(message, "Отлично, секунду...")
            checkin_user(message)
        else:
            bot.reply_to(message, "Занятие завершено")
    else:
        bot.reply_to(message, "Код отметки не подходит")


def checkin_user(message):
    connection = sqlite3.connect("my_database.db")
    cursor = connection.cursor()
    usr_id = message.from_user.id
    usr_first = message.from_user.first_name
    usr_username = message.from_user.username
    # глобальная отметка
    cursor.execute(
        "SELECT * FROM Users WHERE tgid IS '{tgid}'".format(tgid=str(usr_id))
    )
    users = cursor.fetchall()
    if users == []:
        print("nouser globally")
        cursor.execute(
            "INSERT INTO Users (tgid, username, name, visits) VALUES (?, ?, ?, ?)",
            (str(usr_id), str(usr_username), str(usr_first), 1),
        )
    else:
        print("exists")
        cursor.execute(
            "SELECT visits FROM Users WHERE tgid IS '{tgid}'".format(tgid=str(usr_id))
        )
        user_visits = int(cursor.fetchall()[0][0])
        cursor.execute(
            "UPDATE Users SET visits = ? WHERE tgid = ?", (user_visits + 1, str(usr_id))
        )
    # локальная отметка
    cursor.execute(
        "SELECT * FROM '{table}' WHERE tgid IS '{tgid}'".format(
            tgid=str(usr_id), table=message.text
        )
    )
    users = cursor.fetchall()
    if users == []:
        print("nouser locally")
        cursor.execute(
            "INSERT INTO '{table}' (tgid, username, name) VALUES ('{tgid}', '{username}', '{name}')".format(
                table=str(message.text),
                tgid=str(usr_id),
                username=str(usr_username),
                name=str(usr_first),
            )
        )
        
    else:
        print("exists locally")

    connection.commit()
    connection.close()
    bot.reply_to(message, "Отлично, записали на занятие")


def is_user_exists(tgid, dbname):
    pass


@bot.message_handler(commands=["visits"])
@bot.message_handler(regexp="Мои посещения")
def my_visits(message):
    bot.reply_to(message, "В разработке")


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
        bot.reply_to(message, "Задавай код отметки и дату через пробел")
        bot.register_next_step_handler(message, start_check)
    elif message.text == "2":
        bot.reply_to(message, "Занятие с каким кодом необходимо завершить?")
        bot.register_next_step_handler(message, finish_check)


def start_check(message):
    msg = message.text.split()
    date_check = msg[1]
    code_check = msg[0]
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
                table=str(code_check)
            )
        )
        bot.send_message(usr_id, "Успешно")
    else:
        bot.send_message(usr_id, "Занято")
    connection.commit()
    connection.close()


def finish_check(message):
    pass


# если сообщение не распознано
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Я тебя немного не понял. Давай еще раз")


if __name__ == "__main__":
    bot.infinity_polling()
