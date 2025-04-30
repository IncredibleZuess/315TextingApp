import socket, threading, json
import tkinter as tk
from tkinter import simpledialog
from tkinter.scrolledtext import ScrolledText

SERVER_HOST = '127.0.0.1'  # localhost for now
SERVER_PORT = 5000

class ChatClient:
    def __init__(self, master):
        master.title("Tk Chat")
        self.txt = ScrolledText(master, state='disabled', width=50, height=20)
        self.txt.pack(padx=10, pady=5)

        frm = tk.Frame(master)
        tk.Label(frm, text="To (@user or #group):").pack(side='left')
        self.to_var = tk.Entry(frm); self.to_var.pack(side='left', padx=5)
        frm.pack(padx=10, pady=5)

        self.msg_var = tk.Entry(master, width=40)
        self.msg_var.pack(side='left', padx=10)
        self.msg_var.bind('<Return>', lambda e: self.send_message())
        tk.Button(master, text="Send", command=self.send_message).pack(side='left')

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
                if msg['type']=='msg':
                    self.txt.config(state='normal')
                    self.txt.insert('end', f"{msg['from']} → {msg['to']}: {msg['text']}\n")
                    self.txt.yview('end'); self.txt.config(state='disabled')

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
    ChatClient(root)
    root.mainloop()
