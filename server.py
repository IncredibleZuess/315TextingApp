# server.py
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
        for user in list(targets):
            sock = clients.get(user)
            if sock:
                try:
                    sock.sendall(payload)
                except:
                    pass

def broadcast_user_list():
    msg = {'type': 'user_list', 'users': list(clients.keys())}
    broadcast(msg, clients.keys())

def broadcast_group_list():
    msg = {'type': 'group_list', 'groups': list(groups.keys())}
    broadcast(msg, clients.keys())

def handle_client(conn):
    buf = ''
    username = None
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            buf += data
            while '\n' in buf:
                line, buf = buf.split('\n', 1)
                msg = json.loads(line)
                mtype = msg.get('type')

                if mtype == 'register':
                    username = msg.get('username')
                    with lock:
                        clients[username] = conn
                    broadcast_user_list()
                    broadcast_group_list()

                elif mtype == 'join':
                    grp = msg.get('group')
                    with lock:
                        groups.setdefault(grp, set()).add(username)
                    broadcast_group_list()

                elif mtype == 'leave':
                    grp = msg.get('group')
                    with lock:
                        if grp in groups:
                            groups[grp].discard(username)
                            if not groups[grp]:
                                del groups[grp]
                    broadcast_group_list()

                elif mtype == 'msg':
                    to = msg.get('to')
                    if to.startswith('#'):
                        targets = groups.get(to[1:], set())
                    else:
                        targets = {to}
                    msg_obj = {
                        'type': 'msg',
                        'from': username,
                        'to': to,
                        'text': msg.get('text')
                    }
                    broadcast(msg_obj, targets)

    finally:
        removed = False
        with lock:
            if username:
                clients.pop(username, None)
                for grp in list(groups):
                    groups[grp].discard(username)
                    if not groups[grp]:
                        del groups[grp]
                removed = True

        if removed:
            broadcast_user_list()
            broadcast_group_list()

        conn.close()

def main():
    sock = socket.socket()
    sock.bind((HOST, PORT))
    sock.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn, _ = sock.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    main()
