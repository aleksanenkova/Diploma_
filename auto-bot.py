# -*- encoding: utf-8 -*-

import sys
import json
import psycopg2
import traceback

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


class ChatResponder:
    def __init__(self):
        pass
    
    #  def stage_start(self, state, message):
    #      state['stage'] = 'reply1'
    # if message.lower() != u'старт':
    #     state['stage'] = 'reply'
    #           return state, "START: Go to reply"
    #return state, 'START: Какая марка?'
    
    
    def stage_reply1(self, state, message):
        Brand = DB.getBrand(message)
        if Brand is not None:
            str = "Окей, у вас %s \n\nВыберите тип вопроса \n\n1. Поиск детали \n2. Вопрос по ремонту \n3. Обслуживание" % Brand
            state['stage'] = 'reply2'
        else:
            str = "Не удалось распознать марку автомобиля"
            state['stage'] = 'reply1'
        return state, str
    
    
    
    def stage_reply2(self, state, message):
        if message == '1':
            state['stage'] = 'reply3'
            return state, "Введите артикул"
        elif message == '2':
            state['stage'] = 'reply4'
            return state, "Введите узел автомобиля"
        elif message == '3':
            state['stage'] = 'reply5'
            return state, "Введите вопрос по обслуживанию автомобиля"
        elif message == '4':
            state['stage'] = 'reply6'
            return state, "Введите пробег автомобиля"
        else:
            state['stage'] = 'reply2'
            return state, "Сделайте свой выбор поворно"


def proxy(self, state, message):
    
    if message.lower() == u'старт':
        state['stage'] = 'reply1'
        return state, 'Какая марка?'
        
        
        if 'stage' in state:
            
            if state['stage'] == 'reply1':
                return self.stage_reply1(state, message)
            if state['stage'] == 'reply2':
                return self.stage_reply2(state, message)
        state['stage'] = 'start'
        return state, "Undefined stage. Go to stage start"


def handler(chat_state, message):
    new_chat_state, response = {'a': 10}, 'test'
    
    ch = ChatResponder()
    return ch.proxy(chat_state, message)


class DBLayer:
    def __init__(self, db):
        self._db = db
    
    def getState(self, uid):
        with self._db.cursor() as cursor:
            cursor.execute("""
                SELECT state FROM chats WHERE uid = %s LIMIT 1
                """, [uid])
            
            if cursor.rowcount == 1:
                state, = cursor.fetchone()
                return state
            else:
                return {}
    
    
    return None

def getBrand(self, message):
    with self._db.cursor() as cursor:
        cursor.execute("""
            select Auto_name
            from Brand, plainto_tsquery(%s) as query
            where to_tsvector(Brand_name) @@ query = true
            """, [message.lower()])
        if cursor.rowcount == 1:
            str, = cursor.fetchone()
            return str
            else:
                return None

def updateState(self, uid, new_state):
    with self._db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO chats (uid, state) VALUES (%(uid)s, %(new_state)s)
            ON CONFLICT (uid)
            DO UPDATE
            SET state = %(new_state)s,
            updated_at = now()
            """, {'uid': uid, 'new_state': json.dumps(new_state)})


def main(DB, message_handle):
    # Тут запускаем наш цикл работы
    vk_session = vk_api.VkApi(token=config['vk']['token'])
    vk = vk_session.get_api()
    
    longpoll = VkLongPoll(vk_session)
    
    print('Start message handling loop')
    for event in longpoll.listen():
        try:
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                print('Start message handling')
                print('{}: "{}"'.format(event.user_id, event.text), end=' ')
                
                current_state = DB.getState(event.user_id)
                new_chat_state, response = message_handle(current_state, event.text)
                DB.updateState(event.user_id, new_chat_state)
                
                vk.messages.send(
                                 user_id=event.user_id,
                                 message=response
                                 )
        except:
            print('Got unhandled error!!!')
            traceback.print_exc()


if __name__ == '__main__':
    conf_path = sys.argv[1]
    
    config = None
    with open(conf_path, 'r') as F:
        config = json.loads(F.read())

    with psycopg2.connect(
                          "dbname='%(name)s' user='%(login)s' host='%(ip)s' password='%(password)s'" % config['db']
                          ) as db:
        db.autocommit = True
        
        DB = DBLayer(db)
        main(DB, handler)
