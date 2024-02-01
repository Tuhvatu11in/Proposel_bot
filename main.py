import telebot
from telebot import types
import sqlite3

class ProposalBot:
    def __init__(self, token, admin_key, channel_chat_id):
        self.bot = telebot.TeleBot(token)
        self.admin_key = admin_key
        self.channel_chat_id = channel_chat_id
        self.admins = []  # Список зарегистрированных администраторов

    def start(self):
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            if message.chat.id not in self.admins:
                # Обработка сообщений пользователей
                self.handle_user_message(message)
            else:
                # Обработка сообщений администраторов
                self.handle_admin_message(message)

        self.bot.polling()

    def handle_user_message(self, message):
        # Если отправитель - не администратор
        if message.text == self.admin_key:
            # Регистрация нового администратора
            self.admins.append(message.chat.id)
        else:
            # Сохранение предложения
            self.save_proposal(message.text)
            # Уведомление всех администраторов о новом предложении
            self.notify_admins("New proposal")

    def handle_admin_message(self, message):
        if message.text == "Review":
            proposal = self.get_next_proposal()
            if proposal:
                # Отображение следующего предложения для рассмотрения
                self.show_proposal(proposal, message.chat.id)
                # Запрос решения администратора для публикации
                self.prompt_publish_decision(message.chat.id, proposal)

    def save_proposal(self, text):
        # Сохранение предложения в базе данных
        conn = sqlite3.connect('proposals.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO proposals (message) VALUES (?)', (text,))
        conn.commit()
        conn.close()

    def notify_admins(self, text):
        # Уведомление всех администраторов
        for admin in self.admins:
            self.bot.send_message(admin, text)

    def get_next_proposal(self):
        # Получение следующего предложения из базы данных
        conn = sqlite3.connect('proposals.db')
        cursor = conn.cursor()
        cursor.execute('SELECT message FROM proposals')
        proposal = cursor.fetchone()
        conn.close()
        return proposal

    def show_proposal(self, proposal, chat_id):
        # Отображение предложения для рассмотрения
        self.bot.send_message(chat_id, proposal[0])

    def prompt_publish_decision(self, chat_id, proposal):
        # Запрос решения для публикации
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item2 = types.KeyboardButton("👍")
        item3 = types.KeyboardButton("👎")
        keyboard.add(item2, item3)
        self.temp_prop = proposal[0]
        self.bot.send_message(chat_id, 'Publish?', reply_markup=keyboard)

    def publish_proposal(self, decision, chat_id):
        if decision == "👍":
            # Публикация предложения в канале
            self.bot.send_message(self.channel_chat_id, self.temp_prop)
        self.delete_proposal()  # Удаление рассмотренного предложения
        self.bot.send_message(chat_id, 'Decision accepted')

    def delete_proposal(self):
        # Удаление рассмотренного предложения из базы данных
        conn = sqlite3.connect('proposals.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM proposals LIMIT 1')
        conn.commit()
        conn.close()

# Создаем экземпляр класса ProposalBot и запускаем бота
bot = ProposalBot('YOUR_BOT_TOKEN', 'YOUR_ADMIN_KEY', 'YOUR_CHANNEL_ID')
bot.start()
