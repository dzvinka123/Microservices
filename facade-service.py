import json
import random
import uuid
import logging
from flask import Flask, Response, request
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # type: ignore

from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['localhost:29092', 'localhost:39092', 'localhost:49092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

facade_service = Flask(__name__)
config_service = "http://127.0.0.1:8006/config"

def create_retry_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    return session

session = create_retry_session()


def get_service_addresses(service_name):
    try:
        response = session.get(f"{config_service}/{service_name}", timeout=5)
        if response.status_code == 200:
            return response.json().get("addresses", [])
    except requests.exceptions.RequestException as e:
        logging.error(f"[Facade Service] Failed to retrieve addresses for {service_name}. Status code: {response.status_code}")
        logging.error(f"[Facade Service] Request failed: {e}")
        return []

@facade_service.route('/send', methods=['POST'])
def send_message():
    """
    Handles POST requests from the client.
    Generates a UUID for the message and sends it to the logging service.
    If the selected logging service is unavailable, retries with another service.
    """
    msg = request.json.get("msg", "")
    producer.send('messages-topic', value=msg)

    message_id = str(uuid.uuid4())
    logging.info(f"[Facade Service] Received message: {msg}, generated ID: {message_id}")

    logging_services = get_service_addresses("logging-service")
    if not logging_services:
        logging.error("[Facade Service] Cannot get IP Address for Logging Services.")
        return Response("Logging services not available", status=500)

    random.shuffle(logging_services)
    
    for logging_service_url in logging_services:
        try:
            logging.info(f"[Facade Service] Trying to send message to {logging_service_url}...")
            response = requests.post(logging_service_url, json={"id": message_id, "msg": msg}, timeout=5)
            
            logging.info(f"[Facade Service] Response from {logging_service_url}: {response.status_code}")
            
            if response.status_code == 200:
                logging.info(f"[Facade Service] Message sent successfully to {logging_service_url}")
                return Response(status=200)
            else:
                logging.warning(f"[Facade Service] Failed to send message, status code: {response.status_code}")
                continue

        except requests.exceptions.RequestException as e:
            logging.error(f"[Facade Service] Failed to connect to {logging_service_url}: {e}")
            continue

    logging.error("[Facade Service] All logging services are unavailable.")
    return Response("Error sending message. All logging services are unavailable.", status=500)


@facade_service.route('/retrieve', methods=['GET'])
def retrieve_messages():
    """
    Handles GET requests from the client.
    Fetches logs from the logging service and a static message from the messages service.
    If logging services are unavailable, tries the next one. 
    Returns an error if none are available.
    """
    logging.info("[Facade Service] Retrieving messages from Logging and Messages Services...")

    logging_services = get_service_addresses("logging-service")
    if not logging_services:
        logging.error("[Facade Service] Cannot get IP Address for Logging Services.")
        return Response(status=500)
    
    random.shuffle(logging_services)

    message_url = get_service_addresses("messages-service")
    if not message_url:
        logging.error("[Facade Service] Cannot get IP Address for Messages Services.")
        return Response(status=500)

    random.shuffle(message_url)


    for logging_service_url in logging_services:
        try:
            logging_response = requests.get(logging_service_url, timeout=5)
            if logging_response.status_code != 200:
                logging.error(f"[Facade Service] Failed to retrieve messages from {logging_service_url}. Status code: {logging_response.status_code}")
                continue

            message_response = requests.get(message_url[0], timeout=5)
            if message_response.status_code != 200:
                logging.error(f"[Facade Service] Failed to retrieve message from {message_url[0]}. Status code: {message_response.status_code}")
                return Response("Error retrieving message from Messages Service.", 500)
                

            concatenated_response = (
                "Logging Service Response: " + logging_response.text + "; "
                "Messages Service Response: " + message_response.text
            )
            logging.info("[Facade Service] Successfully retrieved logs and message service response.")
            return concatenated_response
        
        except requests.exceptions.RequestException as e:
            logging.error(f"[Facade Service] Request failed to {logging_service_url}: {e}")
            continue

    logging.error("[Facade Service] All logging services are unavailable.")
    return Response("Error retrieving messages. All logging services are unavailable.", 500)


if __name__ == '__main__':
    logging.info("[Facade Service] Starting on port 8000...")
    facade_service.run(port=8000)
