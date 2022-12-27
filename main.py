from datetime import datetime
from random import randrange
from typing import List
import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


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

    def _get_url(self, method: str):
        """Возвращает URL-адрес с передачей метода API"""
        return f'{self.URL}{method}'

    def get_myself_user_info(self, user_id) -> List[dict]:
        """Информация о пользователе"""
        values = {'user_ids': user_id, 'fields': 'bdate, sex, city, status'}
        return self.vk.method(self.METHOD_USERS_GET, values=values)

    def search_users(self, search_criteria: dict) -> 'json':
        """Поиск людей по критериям"""
        city = search_criteria['city']
        sex = 0
        status = 1
        age = search_criteria['age']

        if search_criteria['sex'] == 1:
            sex = 2

        elif search_criteria['sex'] == 2:
            sex = 1

        params = {'fields': 'bdate, city, sex, relation, domain',
                  'city_id': city,
                  'sex': sex,
                  'status': status,
                  'age_from': age,
                  'is_closed': 0,
                  'count': 1000,
                  }

        vk = vk_api.VkApi(token=self.USER_TOKEN)
        response = vk.method(self.METHOD_USERS_SEARCH, values=params)

        return response

    def _get_photos(self, user_id: int):
        """Получает фотографии пользователя."""
        params = {'album_id': 'profile',
                  'owner_id': user_id,
                  'extended': 1}

        vk = vk_api.VkApi(token=self.USER_TOKEN)

        try:
            response = vk.method(self.METHOD_USERS_PHOTOS, values=params)
            return response

        except vk_api.ApiError:
            return 'Нет доступа к фото...'

    def _get_id_city_by_name(self, name_city: str):
        """Получает города из базы"""
        params = {'country_id': 1,
                  'need_all': 1,
                  'count': 1000, }

        vk = vk_api.VkApi(token=self.USER_TOKEN)
        response = vk.method(self.METHOD_CITIES_GET, values=params)
        data_cities = response

        cities_list = data_cities['items']

        for city in cities_list:
            if city['title'] == name_city.capitalize():
                city_id = city['id']
                return int(city_id)

    def get_popular_photos(self, user_id: int) -> dict:
        """Возвращает самые популярные фотографии пользователя"""
        user_photos = self._get_photos(user_id)
        photos_data = {}

        if type(user_photos) == dict:
            try:
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

            except KeyError:
                photos_data[user_id] = {'count': 0}

        else:
            return user_photos

        return photos_data

    def write_msg(self, user_id, message, attachment=None):
        """Отправляет сообщение пользователю"""
        self.vk.method('messages.send', {'user_id': user_id,
                                         'message': message,
                                         'attachment': attachment,
                                         'random_id': randrange(10 ** 7)})

    def greet_msg(self, user_id):
        """Выводит приветственное сообщение"""
        message = """
            Привет!
            Для поиска пары отправьте сообщение с текстом \"поиск\"
            """

        self.write_msg(user_id, message)

    def user_url_msg(self, user_id, message):
        """Отправляет url страницы пользователя"""
        vk_url = 'https://vk.com/'
        vk_url += message
        self.write_msg(user_id, vk_url)

    def search_result_photo_msg(self, user_id, photos=None, message=None):
        """Присылает популярные фотографии"""
        self.write_msg(user_id, message, photos)

    def undefined_msg(self, user_id):
        """Выводит сообщение о непонятной команде"""
        message = "Не поняла вашего ответа..."
        self.write_msg(user_id, message)

    def get_city(self, user_id):
        """Запрашивает город, в котором необходимо осуществить поиск"""
        self.write_msg(user_id, 'Укажите город, в котором необходимо осуществить поиск...')

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    name_city = event.text
                    city_id = self._get_id_city_by_name(name_city)

                    return city_id

    def get_age_from(self, user_id, b_date):
        """Выбор возраста"""
        bdate = b_date.split('.')

        if len(bdate) == 3:
            age = datetime.today().year - int(bdate[2])
            return age

        else:
            self.write_msg(user_id, 'Укажите минимальный возраст...')

            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        age_low = event.text
                        return age_low


if __name__ == '__main__':
    bot = VKBot()

    for event in bot.longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text.lower()
                myself_user_id = event.user_id
                bot.greet_msg(myself_user_id) 

                if request == 'поиск':
                    myself_info = bot.get_myself_user_info(myself_user_id)  # сбор информации о пользователе
                    search_criteria = {}

                    # проверка наличия всех необходимых данных
                    myself_info_list = [item for item in myself_info[0]]

                    if 'city' not in myself_info_list:
                        user_city = bot.get_city(myself_user_id)
                        search_criteria['city'] = user_city
                    else:
                        search_criteria['city'] = myself_info[0]['city']['id']

                    sex = myself_info[0]['sex']
                    search_criteria['sex'] = sex
                    age = bot.get_age_from(myself_user_id, myself_info[0]['bdate'])
                    search_criteria['age'] = age

                    searching_people = bot.search_users(search_criteria)  # поиск подходящих пар

                    for i in range(len(searching_people['items'])):
                        user_id = searching_people['items'][i]['id']
                        user_domain = searching_people['items'][i]['domain']

                        # отправляет ссылку на страницу найденного пользователя
                        bot.user_url_msg(myself_user_id, user_domain)
                        photos_info = bot.get_popular_photos(user_id)

                        if type(photos_info) == str:
                            bot.write_msg(myself_user_id, photos_info)
                            continue

                        else:
                            for photo in photos_info:
                                if photos_info[photo] == user_id:
                                    continue

                                else:
                                    bot.search_result_photo_msg(myself_user_id,
                                                                photo,
                                                                user_id)

                else:
                    bot.undefined_msg(myself_user_id)
