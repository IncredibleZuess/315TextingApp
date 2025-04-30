import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 5000

clients = {}      # username → socket
groups  = {}      # groupname → set of usernames
lock    = threading.Lock()

def broadcast(msg_obj, targets):
    payload = (json.dumps(msg_obj) + '\n').encode()
    with lock:
        for user in targets:
            sock = clients.get(user)
            if sock:
                try: sock.sendall(payload)
                except: pass

def handle_client(conn):
    buf = ''
    username = None
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data: break
            buf += data
            while '\n' in buf:
                line, buf = buf.split('\n', 1)
                msg = json.loads(line)
                if msg['type']=='register':
                    username = msg['username']
                    with lock: clients[username]=conn
                elif msg['type']=='join':
                    grp = msg['group']
                    with lock: groups.setdefault(grp,set()).add(username)
                elif msg['type']=='msg':
                    to = msg['to']
                    if to.startswith('#'):
                        targets = groups.get(to[1:],set())
                    else:
                        targets = {to}
                    msg_obj = {'type':'msg','from':username,'to':to,'text':msg['text']}
                    broadcast(msg_obj, targets)
    finally:
        with lock:
            if username:
                clients.pop(username,None)
                for g in groups.values(): g.discard(username)
        conn.close()

def main():
    sock = socket.socket()
    sock.bind((HOST, PORT))
    sock.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn,_ = sock.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__=='__main__':
    main()
