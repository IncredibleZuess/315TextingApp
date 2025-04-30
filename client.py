import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog, StringVar
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

class ChatClient:
    def __init__(self, master):
        master.title("Tk Chat")

        self.latest_users  = []
        self.latest_groups = []

        # 1) Paned window: sidebar + main
        paned = ttk.Panedwindow(master, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # 2) Sidebar (Users + Groups)
        sidebar = ttk.Frame(paned, width=150, padding=5)
        ttk.Label(sidebar, text="Online Users:").pack(anchor='w')
        self.user_listbox = tk.Listbox(sidebar, height=10)
        self.user_listbox.pack(fill='both', expand=True)

        # corrected: apply pady in pack(), not as a widget kw
        ttk.Label(sidebar, text="Available Groups:") \
            .pack(anchor='w', pady=(10,0))
        self.group_listbox = tk.Listbox(sidebar, height=10)
        self.group_listbox.pack(fill='both', expand=True)

        btn_frame = ttk.Frame(sidebar, padding=(5,5))
        ttk.Button(btn_frame, text="Join",
                   command=self.join_selected_group) \
            .pack(side='left', fill='x', expand=True)
        ttk.Button(btn_frame, text="Leave",
                   command=self.leave_selected_group) \
            .pack(side='left', fill='x', expand=True, padx=(5,0))
        btn_frame.pack(fill='x', pady=(5,0))

        paned.add(sidebar, weight=1)

        # 3) Main content (Chat + Input)
        content = ttk.Frame(paned, padding=5)
        paned.add(content, weight=4)

        # Chat history
        self.txt = ScrolledText(content, state='disabled',
                                width=50, height=20,
                                relief='flat', borderwidth=0)
        self.txt.grid(row=0, column=0, columnspan=3,
                      sticky='nsew', pady=(0,10))
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        # Recipient dropdown + New Group…
        ttk.Label(content, text="To:").grid(row=1, column=0, sticky='w')
        self.to_var = StringVar()
        self.recipient_cb = ttk.Combobox(
            content, textvariable=self.to_var,
            state='readonly', width=25
        )
        self.recipient_cb.grid(row=1, column=1, sticky='ew', pady=(0,10))
        ttk.Button(content, text="New Group…",
                   command=self.create_group) \
            .grid(row=1, column=2, sticky='w',
                  padx=(5,0), pady=(0,10))

        # Message entry + Send
        self.msg_var = ttk.Entry(content)
        self.msg_var.grid(row=2, column=0, columnspan=2, sticky='ew')
        self.msg_var.bind('<Return>', lambda e: self.send_message())
        ttk.Button(content, text="Send",
                   command=self.send_message) \
            .grid(row=2, column=2, sticky='w', padx=(5,0))

        # 4) Networking
        self.username = simpledialog.askstring("Username", "Enter a username:")
        self.sock = socket.socket()
        self.sock.connect((SERVER_HOST, SERVER_PORT))
        self._send({'type': 'register', 'username': self.username})

        threading.Thread(target=self.listen_server, daemon=True).start()

    def _send(self, obj):
        self.sock.sendall((json.dumps(obj) + '\n').encode())

    def listen_server(self):
        buf = ''
        while True:
            data = self.sock.recv(1024).decode()
            if not data: break
            buf += data
            while '\n' in buf:
                line, buf = buf.split('\n', 1)
                msg = json.loads(line)
                mtype = msg.get('type')

                if mtype == 'user_list':
                    self.latest_users = msg.get('users', [])
                    self.user_listbox.delete(0, 'end')
                    for u in self.latest_users:
                        self.user_listbox.insert('end', u)
                    self._update_recipient_options()

                elif mtype == 'group_list':
                    self.latest_groups = msg.get('groups', [])
                    self.group_listbox.delete(0, 'end')
                    for g in self.latest_groups:
                        self.group_listbox.insert('end', g)
                    self._update_recipient_options()

                elif mtype == 'msg':
                    sender = msg.get('from')
                    to_raw = msg.get('to')
                    display_to = to_raw if to_raw.startswith('#') else f"@{to_raw}"
                    self.txt.config(state='normal')
                    self.txt.insert(
                        'end',
                        f"{sender} → {display_to}: {msg.get('text')}\n"
                    )
                    self.txt.yview('end')
                    self.txt.config(state='disabled')

    def _update_recipient_options(self):
        opts = [f"@{u}" for u in self.latest_users] + [f"#{g}" for g in self.latest_groups]
        self.recipient_cb['values'] = opts

    def send_message(self):
        sel  = self.to_var.get().strip()
        text = self.msg_var.get().strip()
        if not (sel and text):
            return

        if sel.startswith('#'):
            grp = sel[1:]
            self._send({'type': 'join', 'group': grp})
            to_send = f"#{grp}"
        elif sel.startswith('@'):
            to_send = sel[1:]
        else:
            to_send = sel

        self._send({'type': 'msg', 'to': to_send, 'text': text})
        self.msg_var.delete(0, 'end')

    def join_selected_group(self):
        sel = self.group_listbox.curselection()
        if not sel: return
        grp = self.group_listbox.get(sel[0])
        self._send({'type': 'join', 'group': grp})

    def leave_selected_group(self):
        sel = self.group_listbox.curselection()
        if not sel: return
        grp = self.group_listbox.get(sel[0])
        self._send({'type': 'leave', 'group': grp})

    def create_group(self):
        grp = simpledialog.askstring("New Group", "Enter a new group name:")
        if grp:
            self._send({'type': 'join', 'group': grp})

if __name__ == '__main__':
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam')
    ChatClient(root)
    root.mainloop()
