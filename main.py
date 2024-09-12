import threading
import time
import codecs
import json
import schedule
import telebot
import os
import sqlite3 as sl
from sqlite3 import Error

from pyexpat.errors import messages
from telebot import types


token = os.getenv('TOKEN')

bot = telebot.TeleBot(token)


class User:
    def __init__(self, user_id=None, name=None,used_cities=list(),score=0,max_score=0):
        self.user_id=user_id
        self.name=name
        self.used_cities=list(used_cities)
        self.score=score
        self.max_score=max_score

    def update_max_score(self):
        self.max_score=max(self.max_score,self.score)

DATA=[]



@bot.message_handler(commands=['start'])
def start_func(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Играть")
    markup.add(btn1)
    bot.send_message(message.chat.id,
                     text="Здраствуйте, {0.first_name}!\nЭтот бот создан для того чтобы победить тебя в игре в города. Считаешь что это не так? Тогда жми играть и покажи на что ты способен!".format(
                           message.from_user), reply_markup=markup)
    bot.register_next_step_handler(message, reg_game)

def reg_game(message):
    if message.text=="Играть":
        user=(User(user_id=message.chat.id, name=None))
        bot.register_next_step_handler(message, game, user)


def game(message, user):
    print(user.score,user.used_cities)
    city=str(message.text.capitalize())
    if (
            (
                user.score == 0
                or city[0].capitalize()==user.used_cities[-1][-1].capitalize()
                or city[0].capitalize()==user.used_cities[-1][-2].capitalize()
                and user.used_cities[-1][-1] in ['ь','ъ','ы','й']

            )
            and city in data_cities
            and city not in user.used_cities

    ):
        user.used_cities.append(message.text.capitalize())
        user.score+=1
        bot_game(message,user)
    elif str(message.text.capitalize()) in user.used_cities:
        bot.send_message(message.chat.id, 'Этот город уже был, попробуй еще раз')
        bot.register_next_step_handler(message, game, user)
    elif city[0] != user.used_cities[-1][-1].capitalize() and city[0] != user.used_cities[-1][-2].capitalize():
        bot.send_message(message.chat.id, 'Город не на ту букву, попробуй еще раз')
        bot.register_next_step_handler(message, game, user)
    else:
        bot.send_message(message.chat.id, 'Такого города нет, попробуй еще раз')
        bot.register_next_step_handler(message, game, user)

def bot_game(message,user):
    for i in data_cities:
        if (
                i[-1] in ['а','к','о']
                and (
                    i[0]==user.used_cities[-1][-1].capitalize()
                    or user.used_cities[-1][-1] in ['ь','ъ','ы','й']
                    and i[0]==user.used_cities[-1][-2].capitalize()
                )
                and i not in user.used_cities
        ):
            user.used_cities.append(i)
            bot.send_message(user.user_id, f'Город: {i}\nТвой ход!')
            bot.register_next_step_handler(message, game, user)
            break
    else:
        for i in data_cities:
            if (
                    (
                        i[0] == user.used_cities[-1].capitalize()
                        or user.used_cities[-1][-1] in ['ь', 'ъ', 'ы', 'й']
                        and i[0] == user.used_cities[-2].capitalize()
                    )
                    and i not in user.used_cities
            ):
                user.used_cities.append(i)
                bot.send_message(user.user_id, f'Город: {i}\nТвой ход!')
                bot.register_next_step_handler(message, game, user)
                break
        else:
            bot.send_message(user.user_id, 'Ты победил! Игра окончена')


@bot.message_handler(comands=['help'])
def start_help_func(message):
    bot.send_message(message.chat.id,
                     "")

def thread_func():
    while True:
        schedule.run_pending()
        time.sleep(1)

def create_connection(path):
    conn = None
    try:
        conn = sl.connect('reports.db', check_same_thread=False)
        print("Подключение к базе данных SQLite прошло успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")
    return conn



if __name__ == '__main__':

    connection = create_connection("reports.db")


    # функция отправки запросов
    def execute_query(connection, query):
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
            print("Запрос выполнен успешно")
        except Error as e:
            print(f"Произошла ошибка '{e}'")


    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      time TEXT NOT NULL,
      weather INTEGER,
      news INTEGER,
      horoscope INTEGER
    );
    """
    execute_query(connection, create_users_table)

    with codecs.open('cities.json','r',"utf_8_sig") as f:
        fcities = json.load(f)

    a=fcities['city']
    data_cities=list()
    for i in a:
        data_cities.append(str(i['name']))



    bot.polling(none_stop=True)
