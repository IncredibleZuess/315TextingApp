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
                try:
                    sock.sendall(payload)
                except:
                    pass

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
                        grp = "Global" # Create a default group for all users and let them join it on initial connection
                        members = groups.setdefault(grp, set())
                        members.add(username)
                    broadcast({'type':'system',
                               'text':f"{username} has joined the chat"},
                              members) # Notify users that a new user has joined
                    broadcast_user_list()
                    broadcast_group_list()

                elif mtype == 'join':
                    grp = msg['group']
                    # If a user has joined a group, they cannot join it again
                    if username in groups[grp]: #TODO DIE CODE ERROR. Ek dink die dictionary key exist nie voor ons hom check nie so ons moet hom eers add voor ons kan check of die user nie in die groep is nie
                        broadcast({'type':'system',"text":"You have already joined this group"},
                                  {username})
                        break
                    with lock:
                        members = groups.setdefault(grp, set())
                        # if statement tot by die broadcast_group call sal die key error fix
                        if username in members:
                            # already a member—notify only this user (private)
                            try:
                                conn.sendall(
                                  (json.dumps({
                                     'type':'system',
                                     'text':'You have already joined this group'
                                   }) + '\n').encode()
                                )
                            except:
                                pass
                            continue # Break vervang met continue anders kan die user niks anders op system doen as uit loop breek nie
                        members.add(username)

                    # announce to all members (including new joiner)
                    broadcast({'type':'system',
                               'text':f"{username} has joined #{grp}"},
                              members)
                    broadcast_group_list()

                elif mtype == 'leave':
                    grp = msg['group']
                    if grp == "Global":
                            #Cannot leave the global group
                            broadcast({'type':'system',
                                       'text':"SORRY cannot leave global group"},
                                      {username})
                            break
                    with lock:
                        members = groups.get(grp, set())
                        before = set(members)
                        members.discard(username)
                        
                        # if now empty, delete the group
                        if not members:
                            del groups[grp]

                    # notify both the leaver and remaining members
                    notify = before | {username}
                    broadcast({'type':'system',
                               'text':f"{username} has left #{grp}"},
                              notify)
                    broadcast_group_list()

                elif mtype == 'msg':
                    to = msg.get('to')
                    text = msg.get('text')
                    if to.startswith('#'):
                        grp = to[1:]
                        with lock:
                            members = groups.get(grp, set())
                        # block if sender not a member
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
                    
    except ConnectionResetError as error:
        print(f"error: {error}")
        # client disconnected without sending a message but we handle this anyways
        print(f"Client {username} disconnected")
        pass
    finally:
        # clean up on disconnect
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
        threading.Thread(target=handle_client,
                         args=(conn,), daemon=True).start()

if __name__ == '__main__':
    main()
