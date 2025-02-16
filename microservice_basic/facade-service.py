import os
import uuid
import time
import logging
from flask import Flask, Response, request
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # type: ignore

logging.basicConfig(level=logging.DEBUG)

facade_service = Flask(__name__)

def get_logging_service_url():
    return os.getenv("LOGGING_SERVICE_URL", "http://localhost:8001/log")

def get_messages_service_url():
    return os.getenv("MESSAGES_SERVICE_URL", "http://localhost:8002/message")


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

@facade_service.route('/send', methods=['POST'])
def send_message():
    """
    Handles POST requests from the client.
    Generates a UUID for the message and sends it to the logging service.
    """
    msg = request.json.get("msg", "")
    message_id = str(uuid.uuid4())

    logging_service_url = get_logging_service_url()

    logging.info(f"[Facade Service] Received message: {msg}, generated ID: {message_id}")

    try:
        response = session.post(logging_service_url, json={"id": message_id, "msg": msg}, timeout=5)

        
        logging.info(f"[Facade Service] Sent message to Logging Service, response: {response.status_code}")
        
        if response.status_code == 200:
            return Response(status=200)
        else:
            logging.error(f"[Facade Service] Failed to send message, status code: {response.status_code}")
            return Response("Error sending message", status=500)
    
    except requests.exceptions.RequestException as e:
        logging.error(f"[Facade Service] Request failed: {e}")
        return Response("Error sending message", status=500)


@facade_service.route('/retrieve', methods=['GET'])
def retrieve_messages():
    """
    Handles GET requests from the client.
    Fetches logs from the logging service and a static message from the messages service.
    """
    logging.info("[Facade Service] Retrieving messages from Logging and Messages Services...")

    try:
        logging_response = session.get(get_logging_service_url())
        message_response = requests.get(get_messages_service_url())

        if logging_response.status_code == 200 and message_response.status_code == 200:
            concatenated_response = (
                "Logging Service Response: " + logging_response.text + "; "
                "Messages Service Response: " + message_response.text
            )
            logging.info("[Facade Service] Retrieved logs and message service response, concatenating responses.")
        else:
            concatenated_response = "Error: One or both services are unavailable."
        
        return concatenated_response

    except requests.exceptions.RequestException as e:
        logging.error(f"[Facade Service] Request failed: {e}")
        return "Error retrieving messages", 500


if __name__ == '__main__':
    logging.info("[Facade Service] Starting on port 8000...")
    facade_service.run(port=8000)
