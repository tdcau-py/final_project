from random import randrange
from typing import List, Any
import os
import vk_api
from vk_api import ApiError
from vk_api.longpoll import VkLongPoll, VkEventType
from db_manage import add_searching_users, create_table, check_repeated_users


class VKUserAuth:
    """Авторизация пользователя"""
    GROUP_TOKEN = os.getenv('VK_TOKEN')

    if not GROUP_TOKEN:
        GROUP_TOKEN = input('Token: ')

    USER_TOKEN = os.getenv('VK_ACCESS_USER_TOKEN')

    if not USER_TOKEN:
        USER_TOKEN = input('Введите токен пользователя: ')


class VKBot:
    URL = 'https://api.vk.com/method/'
    METHOD_USERS_SEARCH = 'users.search'
    METHOD_USERS_GET = 'users.get'
    METHOD_USERS_PHOTOS = 'photos.get'
    METHOD_CITIES_GET = 'database.getCities'
    VK_API_VERSION = '5.131'
    USER_TOKEN = VKUserAuth.USER_TOKEN
    GROUP_TOKEN = VKUserAuth.GROUP_TOKEN

    def __init__(self):
        self.params = {'access_token': self.USER_TOKEN,
                       'v': self.VK_API_VERSION, }

        self.vk = vk_api.VkApi(token=self.GROUP_TOKEN)
        self.longpoll = VkLongPoll(self.vk)

    def write_msg(self, user_id, message, attachment=None):
        """Отправляет сообщение пользователю"""
        self.vk.method('messages.send', {'user_id': user_id,
                                         'message': message,
                                         'attachment': attachment,
                                         'random_id': randrange(10 ** 7)})

    def get_myself_user_info(self, user_id, field: str = None) -> List[dict]:
        """Информация о пользователе"""
        values = {'user_ids': user_id, 'fields': field}
        return self.vk.method(self.METHOD_USERS_GET, values=values)

    def _get_photos(self, user_id: int):
        """Получает фотографии пользователя."""
        params = {'album_id': 'profile',
                  'owner_id': user_id,
                  'extended': 1}

        vk = vk_api.VkApi(token=self.USER_TOKEN)

        try:
            response = vk.method(self.METHOD_USERS_PHOTOS, values=params)
            return response

        except vk_api.ApiError as error:
            return error

    def get_popular_photos(self, user_id: int) -> str | ApiError | dict[str, dict[str, Any]] | Any:
        """Возвращает самые популярные фотографии пользователя"""
        user_photos = self._get_photos(user_id)
        photos_data = {}

        if type(user_photos) == dict:
            if user_photos['count'] > 0:
                for item in user_photos['items']:
                    if len(photos_data) < 3:
                        photos_data[f'photo{item["owner_id"]}_{item["id"]}'] = {'likes': item['likes']['count'],
                                                                                'comments': item['comments']['count'], }

                    else:
                        for photo_data in photos_data:
                            if item['likes']['count'] > photos_data[photo_data]['likes'] and \
                                    item['comments']['count'] > photos_data[photo_data]['comments']:
                                photos_data.pop(photo_data)
                                photos_data[f'photo{item["owner_id"]}_{item["id"]}'] = {'likes': item['likes']['count'],
                                                                                        'comments': item['comments']['count']}
                                break

                            elif item['likes']['count'] > photos_data[photo_data]['likes'] and \
                                    item['comments']['count'] == photos_data[photo_data]['comments']:
                                photos_data.pop(photo_data)
                                photos_data[f'photo{item["owner_id"]}_{item["id"]}'] = {'likes': item['likes']['count'],
                                                                                        'comments': item['comments']['count']}
                                break

                            elif item['likes']['count'] == photos_data[photo_data]['likes'] and \
                                    item['comments']['count'] > photos_data[photo_data]['comments']:
                                photos_data.pop(photo_data)
                                photos_data[f'photo{item["owner_id"]}_{item["id"]}'] = {'likes': item['likes']['count'],
                                                                                        'comments': item['comments']['count']}
                                break

        else:
            return user_photos

        return photos_data

    def _get_id_city_by_name(self, name_city: str):
        """Получает города из базы"""
        params = {'country_id': 1,
                  'need_all': 1,
                  'count': 1000, }

        vk = vk_api.VkApi(token=self.USER_TOKEN)
        response = vk.method(self.METHOD_CITIES_GET, values=params)
        cities_list = response['items']

        for city in cities_list:
            if city['title'] == name_city.capitalize():
                city_id = city['id']
                return int(city_id)

    def get_city(self, user_id):
        """Запрашивает город, в котором необходимо осуществить поиск"""
        try:
            city = self.get_myself_user_info(user_id, 'city')
            city_id = city[0]['city']['id']
            return city_id

        except Exception:
            self.write_msg(user_id, 'Укажите город, в котором необходимо осуществить поиск...')

            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        name_city = event.text
                        city_id = self._get_id_city_by_name(name_city)

                        return city_id

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
        try:
            sex = self.get_myself_user_info(user_id, 'sex')

            if sex[0]['sex'] == 1:
                return 2

            elif sex[0]['sex'] == 2:
                return 1

        except vk_api.ApiError:
            self.write_msg(user_id, 'Укажите пол (мужской/женский) для поиска...')

            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        sex = event.text.lower()

                        if sex == 'мужской':
                            return 2

                        elif sex == 'женский':
                            return 1

    def search_users(self, city, sex, age_from, age_to, status=1) -> dict:
        """Поиск людей по критериям"""
        params = {'fields': 'bdate, city, sex, relation, domain',
                  'city_id': city,
                  'sex': sex,
                  'status': status,
                  'age_from': age_from,
                  'age_to': age_to,
                  'is_closed': 0,
                  'count': 1000,
                  }

        vk = vk_api.VkApi(token=self.USER_TOKEN)
        response = vk.method(self.METHOD_USERS_SEARCH, values=params)

        return response

    def greet_msg(self, user_id):
        """Выводит приветственное сообщение"""
        message = """
            Привет!
            Для поиска пары отправьте сообщение с текстом \"поиск\"
            """

        self.write_msg(user_id, message)

    def search_result_photo_msg(self, user_id, photos):
        """Присылает популярные фотографии"""
        self.vk.method('messages.send', {'user_id': user_id,
                                         'attachment': photos,
                                         'random_id': randrange(10 ** 7)})

    def undefined_msg(self, user_id):
        """Выводит сообщение о непонятной команде"""
        message = "Не поняла вашего ответа..."
        self.write_msg(user_id, message)


if __name__ == '__main__':
    import sqlalchemy
    from sqlalchemy.orm import sessionmaker

    LOGIN = os.getenv('DB_LOGIN')
    PASSWORD = os.getenv('DB_PASSWORD')
    HOST = os.getenv('DB_HOST')
    PORT = os.getenv('DB_PORT')
    DATABASE = 'vkinder_db'

    DSN = f'postgresql://{LOGIN}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'
    engine = sqlalchemy.create_engine(DSN)

    create_table(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    bot = VKBot()

    my_id = int(input('Введите свой ID профиля Вконтакте: '))
    bot.greet_msg(my_id)

    for event in bot.longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text.lower()
                myself_user_id = event.user_id

                if request == 'поиск':
                    city_id = bot.get_city(myself_user_id)
                    sex = bot.get_sex(myself_user_id)
                    age_from = bot.get_age_from(myself_user_id)
                    age_to = bot.get_age_to(myself_user_id)

                    searching_people = bot.search_users(city_id, sex, age_from, age_to)  # поиск подходящих пар

                    for i in range(len(searching_people['items'])):
                        user_id = searching_people['items'][i]['id']
                        user_domain = searching_people['items'][i]['domain']
                        first_name = searching_people['items'][i]['first_name']
                        last_name = searching_people['items'][i]['last_name']
                        user_url_page = 'https://vk.com/' + user_domain
                        repeat_user = check_repeated_users(session, user_id)

                        if not repeat_user:
                            # добавляет пользователя в базу данных
                            add_searching_users(session, first_name, last_name, user_id, user_url_page)

                            # отправляет ссылку на страницу найденного пользователя
                            bot.write_msg(myself_user_id, user_url_page)

                            # отфильтровывает и отправляет 3 популярные фотографии
                            photos_info = bot.get_popular_photos(user_id)

                            if type(photos_info) == str:
                                bot.write_msg(myself_user_id, photos_info)
                                continue

                            else:
                                try:
                                    for photo in photos_info:
                                        if photos_info[photo] == user_id:
                                            continue

                                        else:
                                            bot.search_result_photo_msg(myself_user_id,
                                                                        photo, )

                                except TypeError:
                                    bot.write_msg(myself_user_id, 'Закрытый профиль.')

                        else:
                            continue

                else:
                    bot.undefined_msg(myself_user_id)
