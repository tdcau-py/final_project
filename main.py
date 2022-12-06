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
    VK_API_VERSION = '5.131'

    def __init__(self, id):
        self.id = id

    def _get_url(self, method: str):
        return f'{self.URL}{method}'

    def get_myself_user_info(self, vk):
        """Информация о пользователе"""
        values = {'user_ids': self.id, 'fields': 'bdate, sex, city, relation'}
        return vk.method(self.METHOD_USERS_GET, values=values)

    def search_users(self, group_id: int):
        """Поиск людей по критериям"""
        url = self._get_url(self.METHOD_USERS_SEARCH)
        params = {'access_token': self.USER_TOKEN,
                  'v': self.VK_API_VERSION,
                  'group_id': group_id,
                  'fields': 'photo_max, photo_id',
                  }
        response = requests.get(url, params=params)

        return response.json()


def write_msg(vk, user_id, message, photo_id: str = None):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),
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
                    vk_user = VKUser(event.user_id)
                    myself_info = vk_user.get_myself_user_info(vk_session.vk)
                    searching_people = vk_user.search_users(217477914)
                    # write_msg(vk_session.vk, event.user_id, myself_info[0]['first_name'])
                    print(searching_people)
                    write_msg(vk_session.vk, event.user_id,
                              searching_people['response']['items'][0]['id'],
                              searching_people['response']['items'][0]['photo_id'])
                else:
                    write_msg(vk_session.vk, event.user_id, "Не поняла вашего ответа...")
                