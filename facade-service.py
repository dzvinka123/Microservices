import os
import random
import uuid
import logging
from flask import Flask, Response, request
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # type: ignore

logging.basicConfig(level=logging.DEBUG)

facade_service = Flask(__name__)

logging_services = [
    "http://127.0.0.1:8001/log",
    "http://127.0.0.1:8002/log",
    "http://127.0.0.1:8003/log"
]

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

def get_messages_service_url():
    return os.getenv("MESSAGES_SERVICE_URL", "http://localhost:8004/message")


@facade_service.route('/send', methods=['POST'])
def send_message():
    """
    Handles POST requests from the client.
    Generates a UUID for the message and sends it to the logging service.
    If the selected logging service is unavailable, retries with another service.
    """
    msg = request.json.get("msg", "")
    message_id = str(uuid.uuid4())
    logging.info(f"[Facade Service] Received message: {msg}, generated ID: {message_id}")

    random.shuffle(logging_services)
    for logging_service_url in logging_services:
        try: 
            response = session.post(logging_service_url, json={"id": message_id, "msg": msg}, timeout=5)
            
            logging.info(f"[Facade Service] Sending message to Logging Service, response: {response.status_code}")
            
            if response.status_code == 200:
                logging.info(f"[Facade Service] Message sent to {logging_service_url}")
                return Response(status=200)
            else:
                logging.error(f"[Facade Service] Failed to send message, status code: {response.status_code}")
                return Response("Error sending message", status=500)
        
        except requests.exceptions.RequestException as e:
            logging.error(f"[Facade Service] Request failed: {e}")

    logging.error(f"[Facade Service] All logging services are unavailable.")
    return Response("Error sending message. All logging services are unavailable.", status=500)

@facade_service.route('/retrieve', methods=['GET'])
def retrieve_messages():
    """
    Handles GET requests from the client.
    Fetches logs from the logging service and a static message from the messages service.
    """
    logging.info("[Facade Service] Retrieving messages from Logging and Messages Services...")

    available_services = logging_services[:]
    while available_services:
        logging_service_url = random.choice(available_services)
        logging_response = session.get(logging_service_url)
        message_url = get_messages_service_url()
        message_response = requests.get(message_url)

        if logging_response.status_code != 200:
            logging.error(f"[Facade Service] Failed to retrieve messages from {logging_service_url}. Status code: {logging_response.status_code}")
            available_services.remove(logging_service_url)
        elif message_response.status_code != 200:
            logging.error(f"[Facade Service] Failed to retrieve messages from {message_url}. Status code: {message_response.status_code}")
        else:
            concatenated_response = (
                "Logging Service Response: " + logging_response.text + "; "
                "Messages Service Response: " + message_response.text
            )
            logging.info("[Facade Service] Successfully retrieved logs and message service response.")
            return concatenated_response

    logging.error("[Facade Service] All logging services are unavailable.")
    return "Error retrieving messages. All logging services are unavailable.", 500

if __name__ == '__main__':
    logging.info("[Facade Service] Starting on port 8000...")
    facade_service.run(port=8000)
