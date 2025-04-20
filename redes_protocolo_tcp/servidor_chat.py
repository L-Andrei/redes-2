import socket
import threading
import time

# Configurações do servidor
HOST = '127.0.0.1'
PORT = 65433
BUFFER_SIZE = 1024
SOCKET_TIMEOUT = 30  # Tempo para considerar cliente inativo (em segundos)

# Lista de conexões ativas
clients = {}  # socket -> nickname
last_activity = {}  # socket -> timestamp da última atividade
clients_lock = threading.Lock()

def broadcast(sender_socket, message):
    """Envia mensagem para todos os clientes exceto o emissor"""
    with clients_lock:
        for socket_client, _ in clients.items():
            if socket_client != sender_socket:
                try:
                    socket_client.send(message)
                except:
                    socket_client.close()

def get_socket_by_nickname(nickname):
    """Retorna o socket associado a um nickname (caso exista)"""
    with clients_lock:
        for sock, nick in clients.items():
            if nick == nickname:
                return sock
    return None

def remove_client(client_socket):
    """Remove cliente das estruturas e notifica os outros"""
    with clients_lock:
        if client_socket in clients:
            nickname = clients[client_socket]
            broadcast(client_socket, f">>> {nickname} saiu do chat <<<\n".encode('utf-8'))
            del clients[client_socket]
            if client_socket in last_activity:
                del last_activity[client_socket]
        client_socket.close()

def handle_client_connection(client_socket, client_address):
    """Gerencia a conexão com um cliente específico"""
    client_socket.settimeout(SOCKET_TIMEOUT)

    with clients_lock:
        clients[client_socket] = f"user_{client_address[0]}_{client_address[1]}"
        last_activity[client_socket] = time.time()

    nickname = clients[client_socket]

    welcome = (
        f"Bem-vindo ao chat! Você está conectado como {nickname}\n"
        "Comandos disponíveis:\n"
        "/nick <nome> - Alterar seu nome\n"
        "/whisper <usuário> <mensagem> - Enviar mensagem privada\n"
        "/quit - Sair do chat\n"
    )
    client_socket.send(welcome.encode('utf-8'))
    broadcast(client_socket, f">>> {nickname} entrou no chat <<<\n".encode('utf-8'))

    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break

            last_activity[client_socket] = time.time()
            message = data.decode('utf-8').strip()

            if message.startswith('/nick '):
                with clients_lock:
                    new_nickname = message[6:].strip()
                    old_nickname = clients[client_socket]
                    clients[client_socket] = new_nickname
                client_socket.send(f"Seu nome foi alterado para {new_nickname}\n".encode('utf-8'))
                broadcast(client_socket, f">>> {old_nickname} agora é conhecido como {new_nickname} <<<\n".encode('utf-8'))

            elif message.startswith('/whisper '):
                parts = message.split(' ', 2)
                if len(parts) < 3:
                    client_socket.send("Uso correto: /whisper <usuário> <mensagem>\n".encode('utf-8'))
                    continue

                target_nick = parts[1]
                private_message = parts[2]
                target_socket = get_socket_by_nickname(target_nick)

                if target_socket:
                    sender_nick = clients[client_socket]
                    try:
                        target_socket.send(f"[Mensagem privada de {sender_nick}]: {private_message}\n".encode('utf-8'))
                        client_socket.send(f"[Mensagem privada para {target_nick}]: {private_message}\n".encode('utf-8'))
                    except:
                        client_socket.send("Erro ao enviar mensagem privada.\n".encode('utf-8'))
                else:
                    client_socket.send(f"Usuário '{target_nick}' não encontrado.\n".encode('utf-8'))

            elif message == '/quit':
                remove_client(client_socket)
                break

            elif message == '/ping':
                # Cliente enviando sinal de atividade
                client_socket.send(b"/pong\n")

            else:
                with clients_lock:
                    nickname = clients[client_socket]
                broadcast_msg = f"{nickname}: {message}\n"
                broadcast(client_socket, broadcast_msg.encode('utf-8'))

        except socket.timeout:
            client_socket.send("[AVISO] Você foi desconectado por inatividade.\n".encode('utf-8'))
            remove_client(client_socket)
            break
        except:
            remove_client(client_socket)
            break

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"Servidor de chat iniciado em {HOST}:{PORT}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Nova conexão de {addr}")
            client_thread = threading.Thread(
                target=handle_client_connection,
                args=(client_socket, addr)
            )
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServidor encerrado")
    finally:
        with clients_lock:
            for client in list(clients.keys()):
                try:
                    client.send("[SERVIDOR] Encerrando conexões.\n".encode('utf-8'))
                    client.close()
                except:
                    pass
        server_socket.close()

if __name__ == "__main__":
    main()
