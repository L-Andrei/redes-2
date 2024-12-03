import sys
import time
import signal
import socket
import threading

def signal_handler(sig, frame):
    sys.exit(0)

class Proxy:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # criando um socket TCP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reutilizando o socket
        self.ip = "127.0.0.1"
        self.port = 8080
        self.sock.bind((self.ip, self.port))
        self.sock.listen(10)
        start_multirequest = threading.Thread(target=self.multirequest)
        start_multirequest.setDaemon(True)
        start_multirequest.start()
        while 1:
            time.sleep(0.01)
            signal.signal(signal.SIGINT, signal_handler)
    
    def multirequest(self):
        while True:
            (clientSocket, client_address) = self.sock.accept() # estabelece a conexão
            client_process = threading.Thread(target=self.main, args=(clientSocket, client_address))
            client_process.setDaemon(True)
            client_process.start()
            
    def main(self, client_conn, client_addr): # client_conn é a conexão do cliente proxy, como o navegador.
        origin_request = client_conn.recv(4096)
        request = origin_request.decode(encoding="utf-8") # obtém a solicitação do navegador
        first_line = request.split("\r\n")[0] # analisa a primeira linha
        url = first_line.split(" ")[1] # obtém a url
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]
        webserver = ""
        port = -1
        port_pos = temp.find(":")
        webserver_pos = temp.find("/") # encontra o final do servidor web
        if webserver_pos == -1:
            webserver_pos = len(temp)
        if port_pos == -1 or webserver_pos < port_pos: # porta padrão
            port = 80
            webserver = temp[:webserver_pos]
        else: # porta específica
            port = int(temp[(port_pos + 1):])
            webserver = temp[:port_pos]
        server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_conn.settimeout(1000)
        try:
            server_conn.connect((webserver, port)) # "server_conn" conecta ao servidor web público, como www.google.com:443.
        except: # erro de conexão
            client_conn.close()
            server_conn.close()
            return
        if port == 443:
            client_conn.send(b"HTTP/1.1 200 Connection established\r\n\r\n")
            client_conn.setblocking(0)
            server_conn.setblocking(0)
            client_browser_message = b""
            website_server_message = b""
            while 1:
                try:
                    reply = client_conn.recv(1024)
                    if not reply: break
                    server_conn.send(reply)
                    client_browser_message += reply
                except Exception as e:
                    pass
                try:
                    reply = server_conn.recv(1024)
                    if not reply: break
                    client_conn.send(reply)
                    website_server_message += reply
                except Exception as e:
                    pass
            server_conn.shutdown(socket.SHUT_RDWR)
            server_conn.close()
            client_conn.close()
            return
        server_conn.sendall(origin_request)
        while 1:
            # recebe dados do servidor web
            data = server_conn.recv(4096)
            if len(data) > 0:
                client_conn.send(data)  # envia para o navegador
            else:
                break
        server_conn.shutdown(socket.SHUT_RDWR)
        server_conn.close()
        client_conn.close()

Proxy()
