from random import randrange
import  os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


class VKUserAuth:
    """Авторизация пользователя"""
    TOKEN = os.getenv('VK_TOKEN')

    if not TOKEN:
        TOKEN = input('Token: ')

    vk = vk_api.VkApi(token=TOKEN)


def write_msg(vk, user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7), })


if __name__ == '__main__':
    vk_session = VKUserAuth()
    longpoll = VkLongPoll(vk_session.vk)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text

                if request == "привет":
                    write_msg(vk_session.vk, event.user_id, f"Хай, {event.user_id}")
                elif request == "пока":
                    write_msg(vk_session.vk, event.user_id, "Пока((")
                elif request == 'поиск':
                    ...
                else:
                    write_msg(vk_session.vk, event.user_id, "Не поняла вашего ответа...")
                