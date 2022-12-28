import os
from typing import List, Any
from vk_api import vk_api, ApiError


class VKUsersInfo:
    METHOD_USERS_SEARCH = 'users.search'
    METHOD_USERS_GET = 'users.get'
    METHOD_USERS_PHOTOS = 'photos.get'
    METHOD_CITIES_GET = 'database.getCities'
    VK_API_VERSION = '5.131'
    USER_TOKEN = os.getenv('VK_ACCESS_USER_TOKEN')

    def __init__(self):
        self.params = {'access_token': self.USER_TOKEN,
                       'v': self.VK_API_VERSION, }

    def get_myself_user_info(self, user_id, field: str = None) -> List[dict]:
        """Информация о пользователе"""
        values = {'user_ids': user_id, 'fields': field}
        vk = vk_api.VkApi(token=self.USER_TOKEN)
        return vk.method(self.METHOD_USERS_GET, values=values)

    def _get_photos(self, user_id: int) -> dict:
        """Получает фотографии пользователя."""
        params = {'album_id': 'profile',
                  'owner_id': user_id,
                  'extended': 1}

        vk = vk_api.VkApi(token=self.USER_TOKEN)

        try:
            response = vk.method(self.METHOD_USERS_PHOTOS, values=params)
            all_photos = response['items']
            return all_photos

        except KeyError:
            return {}

        except vk_api.ApiError:
            return {}

    def get_popular_photos(self, user_id: int) -> str | ApiError | dict[str, dict[str, Any]] | Any:
        """Возвращает самые популярные фотографии пользователя"""
        user_photos = self._get_photos(user_id)
        photos_data = {}

        if user_photos:
            for item in user_photos:
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

    def get_id_city_from_info(self, user_id: int) -> int:
        """Получает ID города из информации о пользователе"""
        try:
            city_info = self.get_myself_user_info(user_id, 'city')
            city_id = city_info[0]['city']['id']
            return int(city_id)

        except Exception:
            return False

    def get_id_city_by_name(self, name_city: str) -> int | Any:
        """Получает ID города из базы"""
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

    def get_sex(self, user_id):
        """Выбор пола людей для поиска"""
        try:
            sex = self.get_myself_user_info(user_id, 'sex')

            if sex[0]['sex'] == 1:
                return 2

            elif sex[0]['sex'] == 2:
                return 1

        except vk_api.ApiError:
            return 0

    def search_users(self, city, sex, age_from, age_to, offset, status=1) -> dict:
        """Поиск людей по критериям"""
        params = {'fields': 'bdate, city, sex, relation, domain',
                  'city_id': city,
                  'sex': sex,
                  'status': status,
                  'age_from': age_from,
                  'age_to': age_to,
                  'is_closed': 0,
                  'count': 1,
                  'offset': offset,
                  }

        vk = vk_api.VkApi(token=self.USER_TOKEN)
        response = vk.method(self.METHOD_USERS_SEARCH, values=params)

        try:
            result = response['items']
            return result

        except KeyError:
            return {}
