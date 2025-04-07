import socket

def run_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "127.0.0.1"
    port = 1234

    client.connect((server_ip, port))


    while True:
        msg = input("Enter message to send (or 'close' to exit): ")
        client.send(msg.encode("utf-8")[:1024])

        res = client.recv(1024)
        res = res.decode("utf-8")

        if res.lower == "closed":
            print("Server closed")
            return
        print(f"Server response: {res}")

    client.close()
    print("Client closed")

run_client()