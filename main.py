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
        TOKEN = input('Token: ')

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

    def __init__(self, id):
        self.id = id
        self.params = {'access_token': self.USER_TOKEN,
                       'v': self.VK_API_VERSION, }

    def _get_url(self, method: str):
        """Возвращает URL-адрес с передачей метода API"""
        return f'{self.URL}{method}'

    def get_myself_user_info(self, vk) -> List[dict]:
        """Информация о пользователе"""
        values = {'user_ids': self.id, 'fields': 'bdate, sex, city, status'}
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
                        photos_data[item['id']] = {'likes': item['likes']['count'],
                                                   'comments': item['comments']['count'], }

                    else:
                        for photo_data in photos_data:
                            if item['likes']['count'] > photos_data[photo_data]['likes'] and \
                                    item['comments']['count'] > photos_data[photo_data]['comments']:
                                photos_data.pop(photo_data)
                                photos_data[item['id']] = {'likes': item['likes']['count'],
                                                           'comments': item['comments']['count']}
                                break

                            elif item['likes']['count'] > photos_data[photo_data]['likes'] and \
                                    item['comments']['count'] == photos_data[photo_data]['comments']:
                                photos_data.pop(photo_data)
                                photos_data[item['id']] = {'likes': item['likes']['count'],
                                                           'comments': item['comments']['count']}
                                break

                            elif item['likes']['count'] == photos_data[photo_data]['likes'] and \
                                    item['comments']['count'] > photos_data[photo_data]['comments']:
                                photos_data.pop(photo_data)
                                photos_data[item['id']] = {'likes': item['likes']['count'],
                                                           'comments': item['comments']['count']}
                                break
        except KeyError:
            photos_data[user_id] = {'count': 0}

        return photos_data


class VKBot:
    def __init__(self, vk_session, user_id, request: str):
        self.vk = vk_session
        self.id = user_id
        self.request = request.lower()
        self.greet_msg(self.vk, self.id)

        if self.request == 'поиск':
            vk_user = VKUser(event.user_id)  # пользователь, для которого производится поиск пары
            myself_info: List[dict] = vk_user.get_myself_user_info(self.vk)  # сбор информации о пользователе
            self.get_additional_info(self.vk, self.id, myself_info)
            searching_people = vk_user.search_users(myself_info)  # поиск подходящих пар

            for i in range(len(searching_people['response']['items'])):
                user_id = searching_people['response']['items'][i]['id']
                user_domain = searching_people['response']['items'][i]['domain']
                photos_info = vk_user.get_popular_photos(user_id)

                for photo in photos_info:
                    self.search_result_photo_msg(self.vk,
                                                 self.id,
                                                 user_domain,
                                                 f'{user_id}_{photo}')
        else:
            self.undefined_msg(self.vk, self.id)

    def write_msg(self, vk, user_id, message):
        """Отправляет сообщение пользователю"""
        vk.method('messages.send', {'user_id': user_id,
                                    'message': message,
                                    'random_id': randrange(10 ** 7)})

    def greet_msg(self, vk, user_id):
        """Выводит приветственное сообщение"""
        message = """
            Привет!
            Для поиска пары отправьте сообщение с текстом \"поиск\"
            """

        self.write_msg(vk, user_id, message)
        # vk.method('messages.send', {'user_id': user_id,
        #                             'message': message,
        #                             'random_id': randrange(10 ** 7), })

    def search_result_photo_msg(self, vk, user_id, message, photos):
        """Присылает популярные фотографии"""
        vk_site = 'https://vk.com/'
        vk.method('messages.send', {'user_id': user_id,
                                    'message': f'{vk_site}{message}',
                                    'attachment': f'photo{photos}',
                                    'random_id': randrange(10 ** 7), })

    def undefined_msg(self, vk, user_id):
        """Выводит сообщение о непонятной команде"""
        message = "Не поняла вашего ответа..."
        vk.method('messages.send', {'user_id': user_id,
                                    'message': message,
                                    'random_id': randrange(10 ** 7), })

    def get_additional_info(self, vk, user_id, user_info):
        """Проверка пользовательских данных и запрос дополнительной информации"""
        data = user_info[0]

        if not data['bdate']:
            message = 'Введите возраст, с которого начинать поиск (мин. 16): '
            vk.method('messages.send', {'user.id': user_id,
                                        'message': message,
                                        'random_id': randrange(10 ** 7)})


if __name__ == '__main__':
    vk_session = VKUserAuth()
    longpoll = VkLongPoll(vk_session.vk)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text
                bot_msg = VKBot(vk_session.vk, event.user_id, request)
