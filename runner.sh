#!/bin/bash

echo "Starting facade-service.py..."
python3 facade-service.py &
FACADESERVICE_PID=$!
echo "Facade service started with PID $FACADESERVICE_PID"

echo "Starting 3 Hazelcast nodes..."
HAZELCAST_DIR="/Users/dzvina/Desktop/hazelcast-5.5.0"

$HAZELCAST_DIR/bin/hz start &
echo "Hazelcast node 1 started."
sleep 20


$HAZELCAST_DIR/bin/hz start &
echo "Hazelcast node 2 started."
sleep 20


$HAZELCAST_DIR/bin/hz start &
echo "Hazelcast node 3 started."
sleep 20


hazelcast_addresses=("127.0.0.1:5701" "127.0.0.1:5702" "127.0.0.1:5703")
client_port=(8001 8002 8003)

sleep 5

for i in {0..2}
do
  echo "Starting logging service for Hazelcast node ${hazelcast_addresses[$i]}..."
  python3 logging-service.py "${hazelcast_addresses[$i]}" "${client_port[$i]}" &
  python3 messages-service.py &

done

wait
