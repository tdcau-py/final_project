import os
from typing import List

from vk_api import vk_api


class VKBot:
    METHOD_USERS_SEARCH = 'users.search'
    METHOD_USERS_GET = 'users.get'
    METHOD_USERS_PHOTOS = 'photos.get'
    METHOD_CITIES_GET = 'database.getCities'
    VK_API_VERSION = '5.131'
    USER_TOKEN = os.getenv('VK_ACCESS_USER_TOKEN')
    GROUP_TOKEN = os.getenv('VK_TOKEN')

    def __init__(self):
        self.params = {'access_token': self.USER_TOKEN,
                       'v': self.VK_API_VERSION, }

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

        try:
            cities_list = response['items']

            for city in cities_list:
                if city['title'] == name_city.capitalize():
                    city_id = city['id']
                    return int(city_id)

        except KeyError:
            return 'Город не найден...'

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
