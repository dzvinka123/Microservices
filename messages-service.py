import json
import sys
import threading
from flask import Flask
from kafka import KafkaConsumer

if len(sys.argv) != 2:
    print("Usage: python messages-service.py <port>")
    sys.exit(1)

port_name = sys.argv[1]

try:
    port = int(port_name)
except ValueError:
    print(f"Invalid port number: {port_name}")
    sys.exit(1)


consumer = KafkaConsumer(
    'messages-topic',
    bootstrap_servers=['localhost:29092', 'localhost:39092', 'localhost:49092'],
    group_id=f'Messages-Service on port {port}',
    enable_auto_commit=True,
    auto_offset_reset='earliest',
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

received_messages = []
messages_service = Flask(__name__)

def consume_messages():
    for msg in consumer:
        try:
            message_obj = msg.value
            print(f'[Messages Service] Received message: {message_obj}')
            received_messages.append(str(message_obj))
            print(f"[Messages Service {port}] received message: {message_obj}")
        except Exception as e:
            print(f"Failed to process message: {e}")

@messages_service.route('/message', methods=['GET'])
def get_message():
    print("[Messages Service] Returning message response.")
    return ", ".join(received_messages)

if __name__ == '__main__':
    print(f"[Messages Service] Starting on port {port}...")
    consumer_thread = threading.Thread(target=consume_messages, daemon=True)
    consumer_thread.start()
    messages_service.run(port=port)
