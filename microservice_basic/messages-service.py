import logging
from flask import Flask

logging.basicConfig(level=logging.DEBUG)

messages_service = Flask(__name__)

@messages_service.route('/message', methods=['GET'])
def get_message():
    """
    Returns a static response.
    """
    logging.info("[Messages Service] Returning static message response.")
    return "not implemented yet"

if __name__ == '__main__':
    logging.info("[Messages Service] Starting on port 8002...")
    messages_service.run(port=8002)
