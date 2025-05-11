import logging
import json
import sys

from flask import Flask, Response, json, jsonify

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

if len(sys.argv) != 3:
    print("Usage: python config-server.py <path-to-config-file> <port>")
    sys.exit(1)

config_file = sys.argv[1]
port = sys.argv[2]
config_service = Flask(__name__)


def reading_config(file_path):
    """
    Reads a JSON configuration file from the specified file path.
    
    Args:
        file_path (str): The path to the configuration file to be read.
        
    Returns:
        dict: The parsed JSON content of the file, or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


@config_service.route('/config/<service_name>', methods=['GET'])
def get_service_config(service_name):
    """
    Returns all IP Addresses for specific microservice.
    """
    config_data = reading_config(config_file)
    service = config_data.get(service_name)
    if service:
        logging.info(f"[Config Server] Successfully getting all IP Address for service {service_name}.")
        return jsonify(service), 200
    return Response("Service not found", 404)


if __name__ == '__main__':
    logging.info("[Config Server] Starting on port 8005...")
    config_service.run(port=port)