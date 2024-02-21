import os
from telebot import types
import telebot


token = open('tokens/telegram.txt').readline()
admin = open('tokens/admin.txt').readline()
bot = telebot.TeleBot(token)  # инит


@bot.message_handler(commands=['start', 'help'])  # старт
def send_welcome(message):
    usr_id = str(message.from_user.id)  # userid
    usr_name = str(message.from_user.first_name)  # имя юзера
    keyboard = types.ReplyKeyboardMarkup(True)  # генерируем клаву
    butt_check = types.KeyboardButton(text='Отметиться')
    butt_visits = types.KeyboardButton(text='Мои посещения')
    butt_admin = types.KeyboardButton(text='Админство')
    if usr_id == admin:
        keyboard.add(butt_check, butt_visits, butt_admin)
    else:
        keyboard.add(butt_check, butt_visits)
    bot.reply_to(message, "Привет, " + str(message.from_user.first_name), reply_markup=keyboard)  # здороваемся
    bot.reply_to(message, "Добро пожаловать на собрание клуба b0nch_CTF. Отметься, нам очень важно видеть статистику посещаемости. Автор этого творения: @mihailovily")


@bot.message_handler(commands=['check'])
@bot.message_handler(regexp="Отметиться")
def recieve_checkin(message):
    bot.reply_to(message, "Отправь код отметки")
    bot.register_next_step_handler(message, check_checkin)
    # кушаем ответ, пихаем в след функцию

def check_checkin(message):
    usr_id = str(message.from_user.id)
    flag = message.text
    otmetka = False
    files_in_dir = os.popen("ls visits").read()
    if flag in files_in_dir:
        otmetka = True
    bot.reply_to(message, 'Проверка кода...')
    if otmetka is True:
        user_on_para(message, files_in_dir)
    else:
        bot.reply_to(message, 'Код отметки не подходит')


def user_on_para(message, files_in_dir):
    need_to_check = message.text + '.txt'
    usr_id = message.from_user.id
    usr_first = message.from_user.first_name
    info_user = ''
    usr_username = message.from_user.username
    if need_to_check in files_in_dir:
        if prevent_spam(usr_id, need_to_check):
            my_file = open("visits/"+need_to_check, "a+")
            user = [usr_id, usr_first, usr_username]
            for i in user:
                info_user += (str(i) + ' ')
            my_file.write(info_user + '\n')
            my_file.close()
            bot.reply_to(message, 'Записали на занятие')
        else:
            bot.reply_to(message, 'Ты уже записан')
    else:
        bot.reply_to(message, 'Код отметки не подходит')


def prevent_spam(usr_id, need_to_check):
    users_list = open("visits/"+need_to_check).read()
    if str(usr_id) not in users_list:
        return True
    else:
        return False

            
@bot.message_handler(commands=['visits'])
@bot.message_handler(regexp="Мои посещения")
def my_visits(message):
    bot.reply_to(message, "В разработке")


@bot.message_handler(commands=['admin'])
@bot.message_handler(regexp="Админство")
def admin_check(message):
    usr_id = str(message.from_user.id)
    if usr_id == admin:
        bot.reply_to(message, "I'm waiting your magnet link")
        bot.register_next_step_handler(message, send_torrent)

def send_torrent(message):
    usr_id = str(message.from_user.id)
    bot.send_message(usr_id, 'Torrents are under constructon')

# если сообщение не распознано
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Я тебя немного не понял. Давай еще раз")


if __name__ == '__main__':
    bot.infinity_polling()