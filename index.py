#Imports
import socket as skt
# start the server and listen for incoming connections from the socket
def run_server():
    # Create a TCP socket where AF_INET is the address family and SOCK_STREAM is the socket type
    # AF_INET is used for IPv4 addresses and SOCK_STREAM is used for TCP connections
    server = skt.socket(skt.AF_INET, skt.SOCK_STREAM) 

    # Have ip and port as variables so that we can change them before production
    ip = "127.0.0.1"
    port = 1234
    server.bind((ip, port))

    # Listen for incoming connections. TODO change when doing multi-threading
    server.listen(0)
    print(f"Server started at {ip}:{port}")

    # Accept a connection from a client. 
    sock, addr = server.accept()
    print(f"Connection from {addr[0]}:{addr[1]}")

    # Main connection loop 
    while True:
        req = sock.recv(1024)
        req= req.decode("utf-8")

        # Stop the server when the client sends "close"
        # TODO this will not be included when designing the GUI
        if req.lower() == "close":
            sock.send("closed".encode("utf-8"))
            break

        print(f"Received: {req}")

        res = "accepted".encode("utf-8")
        sock.send(res)

    # Free resources
    sock.close()
    server.close()


run_server()