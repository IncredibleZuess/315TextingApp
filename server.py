# server.py
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
    with lock:
        for user in list(targets):
            sock = clients.get(user)
            if sock:
                try: sock.sendall(payload)
                except: pass

def broadcast_user_list():
    broadcast({'type':'user_list',
               'users': list(clients.keys())},
              clients.keys())

def broadcast_group_list():
    broadcast({'type':'group_list',
               'groups': list(groups.keys())},
              clients.keys())

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
                    username = msg['username']
                    with lock:
                        clients[username] = conn
                    broadcast_user_list()
                    broadcast_group_list()

                elif mtype == 'join':
                    grp = msg['group']
                    with lock:
                        members = groups.setdefault(grp, set())
                        members.add(username)
                    # everyone in the group (including new joiner) sees this:
                    broadcast({'type':'system',
                               'text':f"{username} has joined #{grp}"},
                              members)
                    broadcast_group_list()

                elif mtype == 'leave':
                    grp = msg['group']
                    with lock:
                        members = groups.get(grp, set())
                        before = set(members)
                        # remove the user
                        members.discard(username)
                        # if now empty, delete the group
                        if not members:
                            del groups[grp]
                    # notify both remaining members and the leaver
                    notify = before | {username}
                    broadcast({'type':'system',
                               'text':f"{username} has left #{grp}"},
                              notify)
                    broadcast_group_list()

                elif mtype == 'msg':
                    to = msg['to']
                    text = msg.get('text')
                    if to.startswith('#'):
                        grp = to[1:]
                        with lock:
                            members = groups.get(grp, set())
                        # block if sender not in group
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
                # remove from all groups
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
        threading.Thread(target=handle_client,
                         args=(conn,), daemon=True).start()

if __name__ == '__main__':
    main()
