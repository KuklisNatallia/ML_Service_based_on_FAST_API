import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost', 5672)
)
channel = connection.channel()

channel.queue_declare(queue='ml_task_queue', durable=True)

# Тестовые сообщения
for i in range(10):
    message = {
        'user_id': 1,
        'data': [[5.1, 3.5, 1.4, 0.2]]
    }

    # Отправляем сообщение
    channel.basic_publish(
        exchange='',
        routing_key='ml_task_queue',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type='application/json'
        )
    )
    print(f"Сообщение {i+1} отправлено в очередь ml_task_queue")

# Проверяем количество сообщений
queue_info = channel.queue_declare(queue='ml_task_queue', passive=True)
print(f"Сообщений в очереди: {queue_info.method.message_count}")

connection.close()