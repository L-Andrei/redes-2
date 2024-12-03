import socket
import os
import datetime

# Configurações do servidor
HOST = '127.0.0.1'  # Endereço IP do servidor (localhost)
PORT = 8080         # Porta onde o servidor escutará as conexões

# Nome do arquivo padrão
DEFAULT_FILE = "index.html"

# Cria um socket TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)  # Define o limite máximo de conexões pendentes
print(f"Servidor HTTP rodando em http://{HOST}:{PORT}")

def get_http_date():
    """Retorna a data atual no formato HTTP/1.1."""
    now = datetime.datetime.utcnow()
    return now.strftime('%a, %d %b %Y %H:%M:%S GMT')

def load_file(file_path):
    """Carrega o conteúdo do arquivo especificado."""
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file_path, 'rb') as file:
            return file.read()
    return None

try:
    while True:
        # Aguarda uma conexão
        client_socket, client_address = server_socket.accept()
        print(f"Conexão recebida de {client_address}")

        # Recebe os dados da requisição
        request = client_socket.recv(1024).decode('utf-8')
        print(f"Requisição recebida:\n{request}")

        # Extrai o caminho solicitado na requisição
        lines = request.splitlines()
        if len(lines) > 0:
            request_line = lines[0]
            requested_path = request_line.split(' ')[1]

            # Se a URL solicitada for "/", usa o arquivo padrão
            if requested_path == '/':
                requested_path = f"/{DEFAULT_FILE}"

            # Remove o "/" inicial para formar o caminho correto
            file_path = requested_path.lstrip('/')

            # Carrega o arquivo solicitado
            response_body = load_file(file_path)
            if response_body is not None:
                response_headers = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Date: {get_http_date()}\r\n"
                    "Server: SimplePythonHTTPServer/1.0\r\n"
                    "Content-Type: text/html\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "Connection: close\r\n"
                    "Cache-Control: no-cache, no-store, must-revalidate\r\n"
                    "Pragma: no-cache\r\n"
                    "Expires: 0\r\n"
                    "\r\n"
                )
            else:
                # Responde com 404 se o arquivo não for encontrado
                response_body = "<html><body><h1>404 Not Found</h1><p>Arquivo não encontrado.</p></body></html>".encode('utf-8')
                response_headers = (
                    "HTTP/1.1 404 Not Found\r\n"
                    f"Date: {get_http_date()}\r\n"
                    "Server: SimplePythonHTTPServer/1.0\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )

        else:
            # Responde com 400 em caso de erro na requisição
            response_body = "<html><body><h1>400 Bad Request</h1><p>Requisição inválida.</p></body></html>"
            response_headers = (
                "HTTP/1.1 400 Bad Request\r\n"
                f"Date: {get_http_date()}\r\n"
                "Server: SimplePythonHTTPServer/1.0\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            )

        # Envia os cabeçalhos e o corpo da resposta ao cliente
        client_socket.sendall(response_headers.encode('utf-8') + response_body)

        # Fecha a conexão com o cliente
        client_socket.close()

except KeyboardInterrupt:
    print("\nServidor interrompido pelo usuário.")

finally:
    server_socket.close()
    print("Servidor encerrado.")