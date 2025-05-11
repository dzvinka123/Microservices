#!/bin/bash

services=("hazelcast" "logging-service" "facade-service" "messages-service" "config-service")

for service in "${services[@]}"; do
    pids=$(ps aux | grep "$service" | grep -v grep | awk '{print $2}')
    
    if [ -n "$pids" ]; then
        echo "Killing processes for $service: $pids"
        kill -9 $pids
    else
        echo "No running processes found for $service."
    fi
done

ps aux | grep hazelcast
