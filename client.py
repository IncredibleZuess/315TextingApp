import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog, StringVar
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk


# Palette & Font
BG_COLOR     = "#F2F2F2"     # panel backgrounds
FG_COLOR     = "#202124"     # primary text
ACCENT_COLOR = "#1A73E8"     # buttons & selections
ENTRY_BG     = "#FFFFFF"     # input fields
BUTTON_FG    = "#FFFFFF"     # button text
FONT_FAMILY  = "Segoe UI Variable"
FONT_SIZE    = 10


SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

class ChatClient:
    def __init__(self, master):
        master.title("Tk Chat")

        self.latest_users  = []
        self.latest_groups = []

        # 1) Paned window: sidebar + main content
        paned = ttk.Panedwindow(master, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # 2) Sidebar
        sidebar = ttk.Frame(paned, width=150, padding=5, style="TFrame")
        paned.add(sidebar, weight=1)

        ttk.Label(sidebar, text="Online Users:", style="TLabel")\
            .pack(anchor='w')
        self.user_listbox = tk.Listbox(
            sidebar, height=8,
            bg=ENTRY_BG, fg=FG_COLOR,
            bd=0, highlightthickness=0,
            selectbackground=ACCENT_COLOR,
            selectforeground=BUTTON_FG,
            font=(FONT_FAMILY, FONT_SIZE)
        )
        self.user_listbox.pack(fill='both', expand=True, pady=(0,5))

        ttk.Label(sidebar, text="Available Groups:", style="TLabel")\
            .pack(anchor='w')
        self.group_listbox = tk.Listbox(
            sidebar, height=8,
            bg=ENTRY_BG, fg=FG_COLOR,
            bd=0, highlightthickness=0,
            selectbackground=ACCENT_COLOR,
            selectforeground=BUTTON_FG,
            font=(FONT_FAMILY, FONT_SIZE)
        )
        self.group_listbox.pack(fill='both', expand=True, pady=(0,5))

        btn_frame = ttk.Frame(sidebar, padding=(5,5), style="TFrame")
        ttk.Button(btn_frame, text="Join", command=self.join_selected_group, style="TButton")\
            .pack(side='left', fill='x', expand=True)
        ttk.Button(btn_frame, text="Leave", command=self.leave_selected_group, style="TButton")\
            .pack(side='left', fill='x', expand=True, padx=(5,0))
        btn_frame.pack(fill='x', pady=(0,10))

        # 3) Main content (chat + controls)
        content = ttk.Frame(paned, padding=5, style="TFrame")
        paned.add(content, weight=4)

        # Chat history
        self.txt = ScrolledText(
            content, state='disabled',
            width=50, height=20,
            relief='flat', borderwidth=0,
            bg=ENTRY_BG, fg=FG_COLOR,
            font=(FONT_FAMILY, FONT_SIZE)
        )
        self.txt.grid(row=0, column=0, columnspan=3,
                      sticky='nsew', pady=(0,10))
        content.rowconfigure(0, weight=1)
        content.columnconfigure((0,1), weight=1)

        # Recipient dropdown + New Group
        ttk.Label(content, text="To:", style="TLabel")\
            .grid(row=1, column=0, sticky='w')
        self.to_var = StringVar()
        self.recipient_cb = ttk.Combobox(
            content, textvariable=self.to_var,
            state='readonly', style="TCombobox"
        )
        self.recipient_cb.grid(row=1, column=1, sticky='ew', padx=(0,5))
        ttk.Button(content, text="New Group…", command=self.create_group, style="TButton")\
            .grid(row=1, column=2, sticky='w')

        # Message entry + Send
        self.msg_var = ttk.Entry(content, style="TEntry")
        self.msg_var.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(5,0))
        self.msg_var.bind('<Return>', lambda e: self.send_message())
        ttk.Button(content, text="Send", command=self.send_message, style="TButton")\
            .grid(row=2, column=2, sticky='w', pady=(5,0))

        # 4) Networking
        self.username = simpledialog.askstring("Username", "Enter a username:")
        if not self.username:
            master.destroy()
            return
        
        
        self.sock = socket.socket()
        self.sock.connect((SERVER_HOST, SERVER_PORT))
        self._send({'type':'register', 'username':self.username})
        threading.Thread(target=self.listen_server, daemon=True).start()
        

    def _send(self, msg):
        self.sock.sendall((json.dumps(msg) + '\n').encode())

    def listen_server(self):
        buf = ''
        while True:
            data = self.sock.recv(1024).decode()
            if not data:
                break
            buf += data
            while '\n' in buf:
                line, buf = buf.split('\n', 1)
                msg = json.loads(line)
                m = msg.get('type')

                if m == 'user_list':
                    self.latest_users = msg['users']
                    self.user_listbox.delete(0, 'end')
                    for u in self.latest_users:
                        self.user_listbox.insert('end', u)
                    self._update_recipients()

                elif m == 'group_list':
                    self.latest_groups = msg['groups']
                    self.group_listbox.delete(0, 'end')
                    for g in self.latest_groups:
                        self.group_listbox.insert('end', g)
                    self._update_recipients()

                elif m == 'system':
                    self._append_system(msg['text'])

                elif m == 'msg':
                    frm, to, txt = msg['from'], msg['to'], msg['text']
                    display_to = to if to.startswith('#') else f"@{to}"
                    self._append_message(f"{frm} → {display_to}: {txt}")

    def _update_recipients(self):
        opts = [f"@{u}" for u in self.latest_users] + [f"#{g}" for g in self.latest_groups]
        self.recipient_cb['values'] = opts
        self.recipient_cb.set('#Global')
        if self.to_var.get() not in opts:
            self.to_var.set('')

    def _append_message(self, line):
        self.txt.config(state='normal')
        self.txt.insert('end', line + '\n')
        self.txt.yview('end')
        self.txt.config(state='disabled')

    def _append_system(self, text):
        self._append_message(f"[SYSTEM] {text}")

    def send_message(self):
        sel = self.to_var.get().strip()
        txt = self.msg_var.get().strip()
        if not (sel and txt):
            return

        if sel.startswith('#'):
            to_send = sel
        elif sel.startswith('@'):
            to_send = sel[1:]
        else:
            to_send = sel

        self._send({'type':'msg', 'to':to_send, 'text':txt})
        self.msg_var.delete(0, 'end')

    def join_selected_group(self):
        sel = self.group_listbox.curselection()
        if not sel:
            return
        grp = self.group_listbox.get(sel[0])
        self._send({'type':'join', 'group':grp})

    def leave_selected_group(self):
        sel = self.group_listbox.curselection()
        if not sel:
            return
        grp = self.group_listbox.get(sel[0])
        self._send({'type':'leave', 'group':grp})

    def create_group(self):
        grp = simpledialog.askstring("New Group", "Enter a new group name:")
        if grp:
            self._send({'type':'join', 'group':grp})

if __name__ == '__main__':
    root = tk.Tk()

    # Style setup
    root.configure(bg=BG_COLOR)
    style = ttk.Style(root)
    style.theme_use('clam')
    root.option_add("*Font", f"{{{FONT_FAMILY}}} {FONT_SIZE}")

    style.configure("TFrame",    background=BG_COLOR)
    style.configure("TLabel",    background=BG_COLOR, foreground=FG_COLOR)
    style.configure("TButton",
        background=ACCENT_COLOR, foreground=BUTTON_FG,
        borderwidth=0, padding=(6,4))
    style.map("TButton",
        background=[("active", "#1669C1"), ("disabled", "#A8B8D8")])

    style.configure("TEntry",
        fieldbackground=ENTRY_BG, background=ENTRY_BG,
        foreground=FG_COLOR, borderwidth=1)
    style.map("TEntry",
        highlightcolor=[("focus", ACCENT_COLOR)])

    style.configure("TCombobox",
        fieldbackground=ENTRY_BG, background=ENTRY_BG,
        foreground=FG_COLOR, borderwidth=1)

    ChatClient(root)
    root.mainloop()
