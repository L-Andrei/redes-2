import sys
import time
import signal
import socket
import threading

# Handler para capturar o sinal de interrupção (Ctrl+C)
def signal_handler(sig, frame):
    print("\n[DEBUG] Proxy encerrado pelo usuário.")
    sys.exit(0)

# Classe Proxy para criar um servidor proxy simples
class Proxy:
    def __init__(self):
        # Criação do socket TCP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reuso da porta
        
        # Configuração do endereço e porta
        self.ip = "127.0.0.1"
        self.port = 8080
        self.sock.bind((self.ip, self.port))
        self.sock.listen(10)  # Permitir até 10 conexões simultâneas
        
        print(f"[DEBUG] Proxy iniciado em {self.ip}:{self.port}")
        
        # Iniciar a thread para gerenciar múltiplas requisições
        start_multirequest = threading.Thread(target=self.multirequest)
        start_multirequest.daemon = True  # Usando a forma moderna de definir a thread como daemon
        start_multirequest.start()
        
        # Loop principal para manter o proxy ativo
        while True:
            time.sleep(0.01)
            signal.signal(signal.SIGINT, signal_handler)

    # Método para gerenciar múltiplas conexões simultâneas
    def multirequest(self):
        while True:
            # Aceitar nova conexão de cliente
            clientSocket, client_address = self.sock.accept()
            print(f"[DEBUG] Nova conexão de {client_address[0]}:{client_address[1]}")
            
            # Criar uma nova thread para lidar com a conexão
            client_process = threading.Thread(target=self.main, args=(clientSocket, client_address))
            client_process.daemon = True
            client_process.start()

    # Método principal que lida com a comunicação entre o cliente e o servidor
    def main(self, client_conn, client_addr):
        try:
            # Recebe a solicitação do cliente
            origin_request = client_conn.recv(4096)
            try:
                # Decodifica a solicitação usando UTF-8
                request = origin_request.decode(encoding="utf-8")
            except UnicodeDecodeError:
                # Usa uma codificação alternativa caso UTF-8 falhe
                request = origin_request.decode(encoding="latin1")
            
            print(f"[DEBUG] Requisição recebida de {client_addr[0]}: {request.splitlines()[0]}")
            
            # Analisa a URL da primeira linha da solicitação HTTP
            first_line = request.split("\r\n")[0]
            url = first_line.split(" ")[1]
            
            # Processa a URL para obter o servidor e porta
            http_pos = url.find("://")
            temp = url[(http_pos + 3):] if http_pos != -1 else url
            port_pos = temp.find(":")
            webserver_pos = temp.find("/")
            webserver_pos = webserver_pos if webserver_pos != -1 else len(temp)
            
            if port_pos == -1 or webserver_pos < port_pos:
                port = 80  # Porta padrão
                webserver = temp[:webserver_pos]
            else:
                port = int(temp[(port_pos + 1):])
                webserver = temp[:port_pos]
            
            print(f"[DEBUG] Conectando a {webserver}:{port}")
            
            # Conecta ao servidor web
            server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_conn.settimeout(1000)
            try:
                server_conn.connect((webserver, port))
                print(f"[DEBUG] Conexão estabelecida com {webserver}:{port}")
            except Exception as e:
                print(f"[DEBUG] Falha ao conectar a {webserver}:{port} - {e}")
                client_conn.close()
                server_conn.close()
                return
            
            # Trata conexões HTTPS (porta 443)
            if port == 443:
                client_conn.send(b"HTTP/1.1 200 Connection established\r\n\r\n")
                client_conn.setblocking(0)
                server_conn.setblocking(0)
                while True:
                    try:
                        data = client_conn.recv(1024)
                        if not data: break
                        server_conn.send(data)
                    except:
                        pass
                    try:
                        data = server_conn.recv(1024)
                        if not data: break
                        client_conn.send(data)
                    except:
                        pass
                server_conn.close()
                client_conn.close()
                print(f"[DEBUG] Conexão HTTPS com {client_addr[0]} encerrada.")
                return
            
            # Envia a solicitação original para o servidor web
            server_conn.sendall(origin_request)
            print(f"[DEBUG] Requisição enviada para {webserver}:{port}")
            
            # Encaminha os dados do servidor para o cliente
            while True:
                data = server_conn.recv(4096)
                if len(data) > 0:
                    client_conn.send(data)
                else:
                    break
            print(f"[DEBUG] Resposta de {webserver}:{port} enviada para {client_addr[0]}")
            server_conn.close()
            client_conn.close()
            print(f"[DEBUG] Conexão com {client_addr[0]} encerrada.")
        except Exception as e:
            # Fecha conexões em caso de erro
            print(f"[DEBUG] Erro na conexão com {client_addr[0]}: {e}")
            client_conn.close()

# Inicializa o servidor proxy
Proxy()
