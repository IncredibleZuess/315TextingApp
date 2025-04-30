import socket, threading, json
import tkinter as tk
from tkinter import simpledialog
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk

SERVER_HOST = '127.0.0.1'  # localhost for now
SERVER_PORT = 5000

class ChatClient:
    def __init__(self, master):
        master.title("Tk Chat")

        # 1) Create the paned window
        paned = ttk.Panedwindow(master, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # 2) Left pane (sidebar)
        sidebar = ttk.Frame(paned, width=150, padding=5)
        # Placeholder: a Listbox that we’ll populate later
        self.user_listbox = tk.Listbox(sidebar, height=20)
        self.user_listbox.pack(fill='both', expand=True)
        paned.add(sidebar, weight=1)

        # 3) Right pane (chat + input)
        content = ttk.Frame(paned, padding=5)
        paned.add(content, weight=4)

        # 4) Chat display in right pane
        self.txt = ScrolledText(content,
                                state='disabled',
                                width=50, height=20,
                                relief='flat', borderwidth=0)
        self.txt.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=(0,5))

        # Make that grid cell expand
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)

        # 5) Recipient entry below chat
        ttk.Label(content, text="To (@user or #group):")\
            .grid(row=1, column=0, sticky='w')
        self.to_var = ttk.Entry(content, width=20)
        self.to_var.grid(row=1, column=1, sticky='ew', padx=(5,0), pady=(0,5))

        # 6) Message entry + Send button
        self.msg_var = ttk.Entry(content)
        self.msg_var.grid(row=2, column=0, sticky='ew')
        self.msg_var.bind('<Return>', lambda e: self.send_message())
        ttk.Button(content, text="Send", command=self.send_message)\
            .grid(row=2, column=1, sticky='w', padx=(5,0))

        # 7) Networking (unchanged)…
        self.username = simpledialog.askstring("Username","Enter a username:")
        self.sock = socket.socket()
        self.sock.connect((SERVER_HOST, SERVER_PORT))
        self._send({'type':'register','username':self.username})
        threading.Thread(target=self.listen_server, daemon=True).start()


    def _send(self, obj):
        self.sock.sendall((json.dumps(obj)+'\n').encode())

    def listen_server(self):
        buf = ''
        while True:
            data = self.sock.recv(1024).decode()
            if not data: break
            buf += data
            while '\n' in buf:
                line,buf = buf.split('\n',1)
                msg = json.loads(line)

                if msg['type']=='user_list':
                # clear & refill the sidebar listbox
                    self.user_listbox.delete(0, 'end')
                    for u in msg['users']:
                        self.user_listbox.insert('end', u)
                
                elif msg['type']=='msg':
                    self.txt.config(state='normal')
                    self.txt.insert('end', f"{msg['from']} → {msg['to']}: {msg['text']}\n")
                    self.txt.yview('end')
                    self.txt.config(state='disabled')

    def send_message(self):
        to = self.to_var.get().strip()
        text = self.msg_var.get().strip()
        if to and text:
            if to.startswith('#'):
                self._send({'type':'join','group':to[1:]})
            self._send({'type':'msg','to':to,'text':text})
            self.msg_var.delete(0,'end')

if __name__=='__main__':
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam') # choose other themes to see which fits our app
    ChatClient(root)
    root.mainloop()
