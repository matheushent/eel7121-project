"""
This module serves as the access point for a Raspberry Pi Pico W board.
It functions as an HTTP server and makes requests to other Pico W boards.
"""
import network
import usocket as socket
import ustruct as struct
import ujson as json
from machine import Pin
import time
import uasyncio as asyncio


# Access Point credentials
NETWORK_SSID = "Pico W"
NETWORK_PASSWORD = "1234567890"

# Default sensor status
sensor_temperature = 0

# Function to handle HTTP requests
def handle_http(client, addr):
    global sensor_temperature  # Use the global variable

    request = client.recv(1024)
    request_str = request.decode('utf-8')

    if "POST /temperature" in request_str:
        # Extract the temperature from the query parameters
        query_params = request_str.split('?')[1]
        params_dict = dict(param.split('=') for param in query_params.split('&'))
        new_temperature = params_dict.get('value', 0)

        # Update the sensor temperature
        sensor_temperature = new_temperature

        # Send the updated HTML content as the HTTP response
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        client.send(response.encode())

    elif "GET /" in request_str or "GET /index.html" in request_str:
        # Serve the default HTML content
        with open('index.html', 'r') as file:
            content = file.read()
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        response += content.replace('{{sensor_temperature}}', str(sensor_temperature))
        client.send(response.encode())
    else:
        # Respond with a 404 error for unknown paths
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
        client.send(response.encode())

    client.close()

# Access Point mode setup
wlan = network.WLAN(network.AP_IF)
wlan.config(essid=NETWORK_SSID, password=NETWORK_PASSWORD)
wlan.active(True)
ip = wlan.ifconfig()[0]
print(f"AP available at {ip}")

# HTTP server setup
http_server = socket.socket()
http_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
http_server.bind(socket.getaddrinfo(ip, 80)[0][-1])  # HTTP server on port 80
http_server.listen(1)
print("HTTP server started")

# List to store WebSocket clients
ws_clients = []

while True:
    print("Heartbeat")
    # Check for HTTP requests
    try:
        client, addr = http_server.accept()
        print('HTTP request from %s' % str(addr))
        handle_http(client, addr)
    except OSError:
        pass
    finally:
        client.close()

