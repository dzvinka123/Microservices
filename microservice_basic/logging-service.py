import logging
from flask import Flask, Response, jsonify, request

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging_service = Flask(__name__)
temporary_db_logs = {}

@logging_service.route('/log', methods=['POST'])
def logging_message():
    """
    Receives a message with a UUID and stores it in memory.
    """
    data = request.json
    message_id = data["id"]

    if message_id in temporary_db_logs:
        logging.warning(f"[Logging Service] Duplicate message ID: {message_id}. Will not be added!")
        return jsonify({"status": "duplicate"}), 200
    
    temporary_db_logs[data["id"]] = data["msg"]
    logging.info(f"[Logging Service] Logged message: {data['msg']} with ID: {message_id}")
    return Response(status=200)

@logging_service.route('/log', methods=['GET'])
def get_logs():
    """
    Returns all stored messages as a string.
    """
    if not temporary_db_logs:
        logging.info("[Logging Service] No logs available")
        return "No logs available"
    
    logging.info("[Logging Service] Returning stored messages.")
    return ", ".join(temporary_db_logs.values())

if __name__ == '__main__':
    logging.info("Logging Service starting on port 8001...")
    logging_service.run(port=8001)
