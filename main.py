from random import randrange
from typing import List
import requests
import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


class VKUserAuth:
    """Авторизация пользователя"""
    GROUP_TOKEN = os.getenv('VK_TOKEN')

    if not GROUP_TOKEN:
        GROUP_TOKEN = input('Token: ')

    vk = vk_api.VkApi(token=GROUP_TOKEN)


class VKUser:
    """Собирает данные о пользователе"""
    USER_TOKEN = os.getenv('VK_ACCESS_USER_TOKEN')

    if not USER_TOKEN:
        USER_TOKEN = input('Введите токен пользователя: ')

    URL = 'https://api.vk.com/method/'
    METHOD_USERS_SEARCH = 'users.search'
    METHOD_USERS_GET = 'users.get'
    METHOD_USERS_PHOTOS = 'photos.get'
    VK_API_VERSION = '5.131'

    def __init__(self, vk_user_id):
        self.user_id = vk_user_id
        self.params = {'access_token': self.USER_TOKEN,
                       'v': self.VK_API_VERSION, }

    def _get_url(self, method: str):
        """Возвращает URL-адрес с передачей метода API"""
        return f'{self.URL}{method}'

    def get_myself_user_info(self, vk) -> List[dict]:
        """Информация о пользователе"""
        values = {'user_ids': self.user_id, 'fields': 'bdate, sex, city, status'}
        return vk.method(self.METHOD_USERS_GET, values=values)

    def search_users(self, search_criteria: List[dict]) -> 'json':
        """Поиск людей по критериям"""
        city = ''
        sex = 0
        status = 1

        for criteria in search_criteria:
            if criteria['city']:
                city = criteria['city']['id']
            else:
                ...

        url = self._get_url(self.METHOD_USERS_SEARCH)
        params = {'fields': 'bdate, city, sex, relation, domain',
                  'city': city,
                  'sex': 1,
                  'status': status,
                  'count': 1000,
                  }
        response = requests.get(url, params={**self.params, **params})

        return response.json()

    def _get_photos(self, user_id: int):
        """Получает фотографии пользователя."""
        url = self._get_url(self.METHOD_USERS_PHOTOS)
        params = {'album_id': 'profile',
                  'owner_id': user_id,
                  'extended': 1}
        response = requests.get(url, params={**self.params, **params})

        return response.json()

    def get_popular_photos(self, user_id: int) -> dict:
        """Возвращает самые популярные фотографии пользователя"""
        user_photos = self._get_photos(user_id)
        photos_data = {}

        try:
            if user_photos['response']['count'] > 0:
                for item in user_photos['response']['items']:
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

        return photos_data


class VKBot:
    def __init__(self):
        self.vk_auth = VKUserAuth()
        self.vk = self.vk_auth.vk
        self.longpoll = VkLongPoll(self.vk)

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

    def search_result_photo_msg(self, user_id, message, photos):
        """Присылает популярные фотографии"""
        # vk.method('messages.send', {'user_id': user_id,
        #                             'message': message,
        #                             'attachment': f'photo{photos}',
        #                             'random_id': randrange(10 ** 7), })

        self.write_msg(user_id, message, photos)

    def undefined_msg(self, user_id):
        """Выводит сообщение о непонятной команде"""
        message = "Не поняла вашего ответа..."
        self.write_msg(user_id, message)

    def get_additional_info(self, user_id, user_info):
        """Проверка пользовательских данных и запрос дополнительной информации"""
        data = user_info[0]
        ...

    def get_id_photos(self):
        """Возвращает id фотографий найденного человека"""
        ...


if __name__ == '__main__':
    bot = VKBot()

    for event in bot.longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text.lower()
                myself_user_id = event.user_id
                bot.greet_msg(myself_user_id)

                if request == 'поиск':
                    vk_user = VKUser(myself_user_id)  # пользователь, для которого производится поиск пары
                    myself_info = vk_user.get_myself_user_info(bot.vk)  # сбор информации о пользователе
                    bot.get_additional_info(myself_user_id, myself_info)  # проверка наличия всех необходимых данных
                    searching_people = vk_user.search_users(myself_info)  # поиск подходящих пар

                    for i in range(len(searching_people['response']['items'])):
                        user_id = searching_people['response']['items'][i]['id']
                        user_domain = searching_people['response']['items'][i]['domain']
                        bot.user_url_msg(myself_user_id, user_domain)  # отправляет сообщение с url найденного пользователя
                        photos_info = vk_user.get_popular_photos(user_id)

                        for photo in photos_info:
                            bot.search_result_photo_msg(user_id,
                                                        user_domain,
                                                        photo)
                else:
                    bot.undefined_msg(myself_user_id)
