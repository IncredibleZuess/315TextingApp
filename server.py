import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 5000

clients = {}    # username → socket
groups  = {}    # groupname → set of usernames
lock    = threading.Lock()

def broadcast(msg_obj, targets):
    payload = (json.dumps(msg_obj) + '\n').encode()
    # dont keep lock, just a snapshot of the sockets
    with lock:
        socks = [clients[user] for user in list(targets) if user in clients]
    # send without holding the lock
    for sock in socks:
        try:
            sock.sendall(payload)
        except:
            pass

def broadcast_user_list():
    broadcast({'type':'user_list', 'users': list(clients.keys())},
              clients.keys())

def broadcast_group_list():
    broadcast({'type':'group_list', 'groups': list(groups.keys())},
              clients.keys())

def handle_client(conn):
    buf = ''
    username = None
    try:
        while True:
            try:
                data = conn.recv(1024).decode()
            except ConnectionResetError:
                # client closed without warning
                break
            if not data:
                break

            buf += data
            while '\n' in buf:
                line, buf = buf.split('\n', 1)
                msg   = json.loads(line)
                mtype = msg.get('type')

                if mtype == 'register':
                    username = msg.get('username')
                    with lock:
                        # prevent duplicate usernames
                        if username in clients:
                            conn.sendall((json.dumps({
                                'type':'system',
                                'text':'Username already in use—please choose another.'
                            }) + '\n').encode())
                            conn.close()
                            return
                        clients[username] = conn
                        # auto-join default "Global" group
                        members = groups.setdefault("Global", set())
                        members.add(username)
                    broadcast({'type':'system',
                               'text':f"{username} has joined the chat"},
                              members)
                    broadcast_user_list()
                    broadcast_group_list()

                elif mtype == 'join':
                    grp = msg.get('group')
                    with lock:
                        existed = grp in groups
                        members = groups.setdefault(grp, set())
                        # prevent duplicate joins
                        if username in members:
                            conn.sendall((json.dumps({
                                'type':'system',
                                'text':'You have already joined this group'
                            }) + '\n').encode())
                            continue
                        members.add(username)
                    # announce creation vs join
                    if not existed:
                        broadcast({'type':'system',
                                   'text':f"{username} has created and joined #{grp}"},
                                  members)
                    else:
                        broadcast({'type':'system',
                                   'text':f"{username} has joined #{grp}"},
                                  members)
                    broadcast_group_list()

                elif mtype == 'leave':
                    grp = msg.get('group')
                    if grp == "Global":
                        conn.sendall((json.dumps({
                            'type':'system',
                            'text':'You cannot leave the Global group'
                        }) + '\n').encode())
                        continue
                    with lock:
                        before = set(groups.get(grp, set()))
                        members = groups.get(grp, set())
                        members.discard(username)
                        if not members and grp in groups:
                            del groups[grp]
                    notify = before | {username}
                    broadcast({'type':'system',
                               'text':f"{username} has left #{grp}"},
                              notify)
                    broadcast_group_list()

                elif mtype == 'msg':
                    to   = msg.get('to')
                    text = msg.get('text')
                    if to.startswith('#'):
                        grp = to[1:]
                        with lock:
                            members = groups.get(grp, set())
                        if username not in members:
                            continue
                        targets = members
                    else:
                        targets = {to}
                    broadcast({'type':'msg',
                               'from': username,
                               'to': to,
                               'text': text},
                              targets)

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
        threading.Thread(
            target=handle_client,
            args=(conn,),
            daemon=True
        ).start()

if __name__ == '__main__':
    main()
