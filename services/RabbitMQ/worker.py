import modelses, database
import pika
import time
import json
from modelses.models import MLModel, PredictionResult
from modelses.balance import Balance
from modelses.user import User
from sqlmodel import Session, create_engine, text
import os
from database.databases import get_database_engine, get_session

# Ждем инициализации RabbitMQ
time.sleep(15)

rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')

# Настройки подключения к RabbitMQ
connection_params = pika.ConnectionParameters(
    host=rabbitmq_host,
    port=5672,
    virtual_host='/',
    credentials=pika.PlainCredentials(
        username='guest',
        password='guest'
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)

# Инициализация модели и БД
ml_model = MLModel()

def process_prediction(user_id: int, data: list):
    # Обрабатываем одно предсказание
    with get_session() as session:
        try:
            # Получаем пользователя и баланс
            user = session.get(User, user_id)
            balance = session.get(Balance, user_id)
            if not user or not balance:
                print(f'Пользователь {user_id} или баланс не найдены')
                return False

            # Проверяем баланс
            cost = ml_model.get_cost_predict()
            if not balance.has_enough_credits(cost):
                # raise ValueError("Not enough credits")
                print(f"Недостаточно кредитов у пользователя {user_id}")
                return False

            # Делаем предсказание
            predictions = ml_model.predict(data)

            # Сохраняем результат
            prediction = PredictionResult(
                user_id=user_id,
                prediction_rez=json.dumps(predictions),
                cost=cost
            )

            # Обновляем баланс
            balance.update_balance(-cost)
            session.add(prediction)
            session.add(balance)
            session.commit()
            print(f'Предсказание для пользователя {user_id} обработано')
            return True

        except Exception as e:
            print (f'Ошибка при обработке предсказания: {e}')
            session.rollback()
            return False

def callback(ch, method, properties, body):
    # Обрабатываем сообщение из очереди
    try:
        message = json.loads(body)
        user_id = message['user_id']
        data = message['data']
        print(f'Получено сообщение для пользователя {user_id}')
        success=process_prediction(user_id, data)
        if success:
            print(f'Успешно обработано для {user_id}')
        else:
            print(f'Ошибка обработки для {user_id}')

    except Exception as e:
        print(f"Ошибка при обработке сообщения: {e}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    try:
        with get_session() as session:
            # Простой запрос для проверки подключения
            result = session.execute(text("SELECT 1")).scalar()
            print('Подключение к базе данных успешно')
    except Exception as e:
        print(f'Ошибка подключения к базе данных: {e}')
        return

    # Запускаем воркера
    for i in range(10):
        try:
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()

            # Объявляем очередь
            channel.queue_declare(queue='ml_task_queue', durable=True)

            # Настройка fair dispatch
            channel.basic_qos(prefetch_count=1)

            # Подписываемся на очередь
            channel.basic_consume(
                queue='ml_task_queue',
                on_message_callback=callback,
                auto_ack=False
            )

            print("Worker started. Waiting for messages...")
            channel.start_consuming()
            break
        except Exception as e:
            print(f"Ошибка подключения к RabbitMQ (попытка {i+1}/10): {e}")
            time.sleep(5)
    else:
        print("Не удалось подключиться к RabbitMQ после 10 попыток")


if __name__ == "__main__":
    start_worker()