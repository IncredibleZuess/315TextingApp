# Imports
import socket
import tkinter as tk

# Main client function
def run_client():
    # Create a TCP socket where AF_INET is the address family and SOCK_STREAM is the socket type
    # AF_INET is used for IPv4 addresses and SOCK_STREAM is used for TCP connections
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Have ip and port as variables so that we can change them before production
    # TODO change when doing multi-threading
    server_ip = "127.0.0.1"
    port = 1234

    client.connect((server_ip, port))


    # Main connection loop
    while True:
        # TODO this will not be included when designing the GUI
        msg = input("Enter message to send (or 'close' to exit): ")
        # Only send 1024 bytes of data to the server
        client.send(msg.encode("utf-8")[:1024])

        # Only receive 1024 bytes of data from the server
        res = client.recv(1024)
        res = res.decode("utf-8")
        # Stop the client when the server sends "closed"
        if res.lower == "closed":
            print("Server closed")
            break
        print(f"Server response: {res}")
    # Free resources
    client.close()
    print("Client closed")

run_client()