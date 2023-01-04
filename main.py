from random import randrange
import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from db_manage import db_connection, add_searching_users, create_table, check_repeated_users
from api_functions import VKUsersInfo


class VKBot:
    GROUP_TOKEN = os.getenv('VK_TOKEN')

    def __init__(self):
        self.vk = vk_api.VkApi(token=self.GROUP_TOKEN)
        self.longpoll = VkLongPoll(self.vk)

    def write_msg(self, user_id, message):
        """Отправляет сообщение пользователю"""
        self.vk.method('messages.send', {'user_id': user_id,
                                         'message': message,
                                         'random_id': randrange(10 ** 7)})

    def get_city(self, user_id):
        """Запрашивает город, в котором необходимо осуществить поиск"""
        self.write_msg(user_id, 'Укажите город, в котором необходимо осуществить поиск...')

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    name_city = event.text
                    return name_city

    def get_age_from(self, user_id):
        """Выбор возраста"""
        self.write_msg(user_id, 'Укажите минимальный возраст для поиска...')

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    age_low = event.text
                    return age_low

    def get_age_to(self, user_id):
        """Максимальный возраст"""
        self.write_msg(user_id, 'Укажите максимальный возраст для поиска...')

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    age_high = event.text
                    return age_high

    def get_sex(self, user_id):
        """Выбор пола людей для поиска"""
        self.write_msg(user_id, 'Укажите пол (мужской/женский) для поиска...')

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    sex = event.text.lower()

                    if sex == 'мужской':
                        return 2

                    elif sex == 'женский':
                        return 1

    def greet_msg(self, user_id):
        """Выводит приветственное сообщение"""
        message = """
            Используйте следующие команды для управления ботом:
                \"поиск\" - для поиска подходящих пар;
                \"далее\" - для получения следующей анкеты.
            """

        self.write_msg(user_id, message)

    def popular_photo_msg(self, user_id, photos):
        """Присылает популярные фотографии"""
        self.vk.method('messages.send', {'user_id': user_id,
                                         'attachment': photos,
                                         'random_id': randrange(10 ** 7)})

    def undefined_msg(self, user_id):
        """Выводит сообщение о непонятной команде"""
        message = "Не поняла вашего запроса..."
        self.write_msg(user_id, message)

    def return_users_info(self, user_id, city_id, sex, age_from, age_to, offset):
        """Возвращает найденных пользователей по одному"""
        searching_people = users_info.search_users(city_id, sex, age_from, age_to, offset)

        if searching_people:
            for i in range(len(searching_people)):
                user_id = searching_people[i]['id']
                user_domain = searching_people[i]['domain']
                first_name = searching_people[i]['first_name']
                last_name = searching_people[i]['last_name']
                user_url_page = 'https://vk.com/' + user_domain
                repeat_user = check_repeated_users(session, user_id)

                if not repeat_user:
                    # добавляет пользователя в базу данных
                    add_searching_users(session, first_name, last_name, user_id, user_url_page)

                    # отправляет ссылку на страницу найденного пользователя
                    bot.write_msg(myself_user_id, user_url_page)

                    # отфильтровывает и отправляет 3 популярные фотографии
                    photos_info = users_info.get_popular_photos(user_id)

                    if not photos_info:
                        bot.write_msg(myself_user_id, 'Доступ к профилю ограничен...')
                        continue

                    else:
                        for photo in photos_info:
                            if photos_info[photo] == user_id:
                                continue

                            else:
                                bot.popular_photo_msg(myself_user_id,
                                                      photo, )

                else:
                    offset += 1
                    return self.return_users_info(user_id, city_id, sex, age_from, age_to, offset)
        else:
            self.write_msg(user_id, 'Пользователи не найдены...')


if __name__ == '__main__':
    from sqlalchemy.orm import sessionmaker

    engine = db_connection()
    create_table(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    bot = VKBot()
    users_info = VKUsersInfo()
    myself_user_id = os.getenv('VK_PROFILE_ID')

    bot.greet_msg(myself_user_id)

    offset = 1
    city_id = 0
    sex = 0
    age_from = 0
    age_to = 0

    for event in bot.longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text.lower()
                myself_user_id = event.user_id

                if request == 'поиск':
                    city_info = users_info.get_myself_user_info(myself_user_id, 'city')
                    city_id = city_info[0]['city']['id']

                    if not city_id or type(city_id) == str:
                        city = bot.get_city(myself_user_id)
                        city_id = users_info.get_id_city_by_name(city)

                    sex = users_info.get_sex(myself_user_id)

                    if not sex:
                        sex = bot.get_sex(myself_user_id)

                    age_from = bot.get_age_from(myself_user_id)
                    age_to = bot.get_age_to(myself_user_id)
                    bot.return_users_info(myself_user_id, city_id, sex, age_from, age_to, offset)

                elif request == 'далее':
                    offset += 1
                    bot.return_users_info(myself_user_id, city_id, sex, age_from, age_to, offset)

                else:
                    bot.undefined_msg(myself_user_id)
                    bot.greet_msg(myself_user_id)
