from random import randrange
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

    def get_myself_user_info(self, vk):
        """Информация о пользователе"""
        values = {'user_ids': self.id, 'fields': 'bdate, sex, city, status'}
        return vk.method(self.METHOD_USERS_GET, values=values)

    def search_users(self, search_criteria: list) -> 'json':
        """Поиск людей по критериям"""
        city = ''
        sex = 0
        status = 1

        url = self._get_url(self.METHOD_USERS_SEARCH)
        params = {'fields': 'bdate, city, sex, relation, domain',
                  'city': search_criteria[0]['city']['id'],
                  'sex': 1,
                  'status': status
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

    def get_popular_photos(self, user_id: int):
        """Возвращает самые популярные фотографии пользователя"""
        user_photos = self._get_photos(user_id)
        photos_data = {}

        if int(user_photos['response']['count']) > 0:
            for item in user_photos['response']['items']:
                if len(photos_data) < 3:
                    photos_data[item['id']] = {'likes': int(item['likes']['count']),
                                               'comments': int(item['comments']['count'])}

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

        return photos_data


def write_msg(vk, user_id, message, photo_id: str = None):
    vk_site = 'https://vk.com/'
    vk.method('messages.send', {'user_id': user_id, 'message': f'{vk_site}{message}',  'random_id': randrange(10 ** 7),
                                'attachment': f'photo{photo_id}'})


if __name__ == '__main__':
    vk_session = VKUserAuth()
    longpoll = VkLongPoll(vk_session.vk)

    # vk_user = VKUser(749333920)
    # myself_info = vk_user.get_myself_user_info(vk_session.vk, 749333920)
    # print(myself_info)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text

                if request == "привет":
                    write_msg(vk_session.vk, event.user_id, f"Хай, {event.user_id}")
                elif request == "пока":
                    write_msg(vk_session.vk, event.user_id, "Пока((")
                elif request == 'поиск':
                    vk_user = VKUser(event.user_id)  # пользователь, для которого производится поиск пары
                    myself_info = vk_user.get_myself_user_info(vk_session.vk)  # сбор информации о пользователе
                    searching_people = vk_user.search_users(myself_info)  # поиск подходящих пар

                    photos_info = vk_user.get_popular_photos(searching_people['response']['items'][1]['id'])
                    print(photos_info)

                    write_msg(vk_session.vk, event.user_id,
                              searching_people['response']['items'][1]['domain'],
                              searching_people['response']['items'][1]['domain'])
                else:
                    write_msg(vk_session.vk, event.user_id, "Не поняла вашего ответа...")
                