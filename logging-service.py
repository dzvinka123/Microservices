import logging
import sys
from flask import Flask, Response, jsonify, request
import hazelcast

if len(sys.argv) != 3:
    print("Usage: python logging-service.py <hazelcast-node-name> <port>")
    sys.exit(1)

node_name = sys.argv[1]
port_name = sys.argv[2]

try:
    port = int(port_name)
except ValueError:
    print(f"Invalid port number: {port_name}")
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging_service = Flask(__name__)

client = hazelcast.HazelcastClient(cluster_members=[node_name])
messages_map = client.get_map('messages_map').blocking()

@logging_service.route('/log', methods=['POST'])
def logging_message():
    """
    Receives a message with a UUID and stores it in memory.
    """
    data = request.json
    message_id = data["id"]

    if messages_map.contains_key(message_id):
        logging.warning(f"[Logging Service] Duplicate message ID: {message_id}. Will not be added!")
        return jsonify({"status": "duplicate"}), 200
    
    messages_map.put(message_id, data["msg"])
    logging.info(f"[Logging Service] Logged message: {data['msg']} with ID: {message_id}")
    return Response(status=200)

@logging_service.route('/log', methods=['GET'])
def get_logs():
    """
    Returns all stored messages as a string.
    """
    if messages_map.is_empty():
        logging.info("[Logging Service] No logs available")
        return "No logs available"
    
    logging.info("[Logging Service] Returning stored messages.")
    return ", ".join(list(messages_map.values()))

if __name__ == '__main__':
    logging.info(f"Logging Service starting on port {port}...")
    logging_service.run(port=port)
