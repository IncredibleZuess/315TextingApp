import tkinter as tk
import socket as skt

def run_server():
    server = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
    ip = "127.0.0.1"
    port = 1234
    server.bind((ip, port))

    server.listen(0)
    print(f"Server started at {ip}:{port}")

    sock, addr = server.accept()
    print(f"Connection from {addr[0]}:{addr[1]}")

    while True:
        req = sock.recv(1024)
        req= req.decode("utf-8")

        if req.lower() == "close":
            sock.send("closed".encode("utf-8"))
            break

        print(f"Received: {req}")

        res = "accepted".encode("utf-8")
        sock.send(res)
    sock.close()
    server.close()


run_server()