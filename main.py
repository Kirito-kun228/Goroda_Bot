import codecs
import json
import time
import telebot
import os
import sqlite3 as sl
from sqlite3 import Error
from telebot import types

token = os.getenv('TOKEN')

bot = telebot.TeleBot(token)


class User:
    def __init__(self, user_id=None, name=None, used_cities=list(), score=0, max_score=0, dificulty_level=1):
        self.user_id = user_id
        self.name = name
        self.used_cities = list(used_cities)
        self.score = score
        self.max_score = max_score
        self.dificulty_level = dificulty_level

    def update_max_score(self):
        self.max_score = max(self.max_score, self.score)


@bot.message_handler(commands=['help'])
def start_help_func(message):
    bot.send_message(message.chat.id, "Доступные команды отображены на кнопках у вас на экране")


@bot.message_handler(commands=['start'])
def start_func(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Играть")
    btn2 = types.KeyboardButton("Таблица рекордов")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id,
                     text="Здраствуйте, {0.first_name}!\nЭтот бот создан для того чтобы победить тебя в игре в города. Считаешь что это не так? Тогда жми играть и покажи на что ты способен!".format(
                         message.from_user), reply_markup=markup)


@bot.message_handler(content_types=['text'])
def chose_func(message):
    # Получаем пользователя по ID
    user=''
    for i in DATA:
        if int(i.user_id) == int(message.chat.id):
            user = i
    if user!='' and list(user.used_cities)!=list(''.split(",")):  # Если пользователь в игре, перенаправляем на функцию game
        game(message, user)
    elif message.text == "Играть":
        user = User(user_id=message.chat.id, name=message.from_user.first_name)
        info = cursor.execute('SELECT * FROM users WHERE user_id=?', (user.user_id,))
        if info.fetchone() is None:
            create_users = 'INSERT INTO users (user_id, name, used_cities, score, max_score, dificulty_level) VALUES (?, ?, ?, ?, ?, ?)'
            data = [(user.user_id, user.name, ",".join(user.used_cities), user.score, user.max_score, user.dificulty_level)]
            with connection:
                connection.executemany(create_users, data)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Легко")
        btn2 = types.KeyboardButton("Сложно")
        btn3 = types.KeyboardButton("Невозможно")
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, 'Выбери уровень сложности', reply_markup=markup)
        bot.register_next_step_handler(message, dif_lvl, user)
    elif message.text == "Таблица рекордов":
        records(user)
    else:
        bot.send_message(message.chat.id, 'Сообщение не распознано')



def dif_lvl(message, user):
    mes = message.text.capitalize()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Сдаться")
    markup.add(btn1)
    if mes == "Легко":
        user.dificulty_level = 20
        bot.send_message(message.chat.id, 'Чтобы начать играть напиши название любого города!', reply_markup=markup)
        bot.register_next_step_handler(message, game, user)
    elif mes == "Сложно":
        user.dificulty_level = 100
        bot.send_message(message.chat.id, 'Чтобы начать играть напиши название любого города!', reply_markup=markup)
        bot.register_next_step_handler(message, game, user)
    elif mes == "Невозможно":
        user.dificulty_level = 50000
        bot.send_message(message.chat.id, 'Чтобы начать играть напиши название любого города!', reply_markup=markup)
        bot.register_next_step_handler(message, game, user)
    else:
        bot.send_message(message.chat.id, 'Не распознано, попробуй еще раз')
        bot.register_next_step_handler(message, dif_lvl, user)


def game(message, user):
    print(user.score, user.used_cities)
    city = str(message.text.capitalize())
    if (
            (
                    user.score == 0
                    or city[0].capitalize() == user.used_cities[-1][-1].capitalize()
                    or city[0].capitalize() == user.used_cities[-1][-2].capitalize()
                    and user.used_cities[-1][-1] in ['ь', 'ъ', 'ы', 'й']

            )
            and city in data_cities
            and city not in user.used_cities

    ):
        user.used_cities.append(message.text.capitalize())
        user.score += 1
        bot_game(message, user)
    elif message.text.capitalize() == "Сдаться":
        final(user,0)
    elif user.score != 0 and str(message.text.capitalize()) in user.used_cities:
        bot.send_message(message.chat.id, 'Этот город уже был, попробуй еще раз')
        bot.register_next_step_handler(message, game, user)
    elif user.score != 0 and city[0] != user.used_cities[-1][-1].capitalize() and city[0] != user.used_cities[-1][-2].capitalize():
        bot.send_message(message.chat.id, 'Город не на ту букву, попробуй еще раз')
        bot.register_next_step_handler(message, game, user)
    else:
        bot.send_message(message.chat.id, 'Такого города нет, попробуй еще раз')
        bot.register_next_step_handler(message, game, user)


def bot_game(message, user):
    if user.score > user.dificulty_level:
        final(user,1)
    else:
        for i in data_cities:
            if (
                    i[-1] in ['а', 'к', 'о']
                    and (
                    i[0] == user.used_cities[-1][-1].capitalize()
                    or user.used_cities[-1][-1] in ['ь', 'ъ', 'ы', 'й']
                    and i[0] == user.used_cities[-1][-2].capitalize()
            )
                    and i not in user.used_cities
            ):
                user.used_cities.append(i)
                bot.send_message(user.user_id, f'Город: {i}\nТвой ход!')
                sev_game(user)
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
                    sev_game(user)
                    break
            else:
                final(user,1)



def final(user, win):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Играть")
    btn2 = types.KeyboardButton("Таблица рекордов")
    markup.add(btn1, btn2)
    user.used_cities=list()
    user.max_score=max(int(user.score), int(user.max_score))
    user.score=0
    user.dificulty_level=0
    update_users = 'UPDATE users SET used_cities=?, score=?, max_score=?, dificulty_level=? WHERE user_id=?'
    data = [
        (",".join(user.used_cities), user.score, user.max_score, user.dificulty_level, user.user_id)
    ]
    with connection:
        connection.executemany(update_users, data)
    if win == 1:
        bot.send_message(user.user_id,
                     'Ты победил! Игра окончена. Можешь гордиться этим. Чтобы начать новую игру нажмите Играть снова',
                     reply_markup=markup)
    else:
        bot.send_message(user.user_id, 'Ха-Ха-Ха Я снова победил!', reply_markup=markup)

def records(user):
    request_to_read_data = "SELECT name, max_score FROM users"
    cursor = connection.cursor()
    cursor.execute(request_to_read_data)
    data = cursor.fetchall()
    data.sort(key=lambda x: x[1], reverse=True)
    str_records=''
    for i in range(len(data)):
        str_records=str_records+f'{i+1}. {data[i][0]} {data[i][1]} \n'
    bot.send_message(user.user_id, f"Таблица рекордов:\n{str_records}")


def sev_game(user):
    update_users = 'UPDATE users SET used_cities=?, score=?, max_score=?, dificulty_level=? WHERE user_id=?'
    data = [
        (",".join(user.used_cities), user.score, user.max_score, user.dificulty_level, user.user_id)
    ]
    with connection:
        connection.executemany(update_users, data)
    bot.register_next_step_handler_by_chat_id(user.user_id, game, user)


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
      name TEXT NOT NULL,
      used_cities TEXT,
      score INTEGER,
      max_score INTEGER,
      dificulty_level INTEGER
    );
    """
    execute_query(connection, create_users_table)

    with codecs.open('cities.json', 'r', "utf_8_sig") as f:
        fcities = json.load(f)
    a = fcities['city']
    data_cities = list()

    for i in a:
        data_cities.append(str(i['name']))

    DATA = []

    request_to_read_data = "SELECT * FROM users"
    cursor = connection.cursor()
    cursor.execute(request_to_read_data)
    data = cursor.fetchall()

    for i in range(len(data)):
        user = User(user_id=data[i][1],
                    name=data[i][2],
                    used_cities=list(data[i][3].split(",")),
                    score=data[i][4],
                    max_score=data[i][5],
                    dificulty_level=data[i][6], )
        DATA.append(user)

    bot.polling(none_stop=True)  # Основной цикл прослушивания


