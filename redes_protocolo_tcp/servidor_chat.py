import socket
import threading

# Configurações do servidor
HOST = '127.0.0.1'
PORT = 65433
BUFFER_SIZE = 1024

# Lista de conexões ativas
clients = {}  # socket -> nickname
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


def handle_client_connection(client_socket, client_address):
    """Gerencia a conexão com um cliente específico"""
    with clients_lock:
        clients[client_socket] = f"user_{client_address[0]}_{client_address[1]}"

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
                with clients_lock:
                    nickname = clients[client_socket]
                    broadcast(client_socket, f">>> {nickname} saiu do chat <<<\n".encode('utf-8'))
                    del clients[client_socket]
                client_socket.close()
                break

            else:
                with clients_lock:
                    nickname = clients[client_socket]
                broadcast_msg = f"{nickname}: {message}\n"
                broadcast(client_socket, broadcast_msg.encode('utf-8'))

        except:
            with clients_lock:
                if client_socket in clients:
                    nickname = clients[client_socket]
                    broadcast(client_socket, f">>> {nickname} saiu do chat <<<\n".encode('utf-8'))
                    del clients[client_socket]
            client_socket.close()
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
            for client in clients:
                try:
                    client.close()
                except:
                    pass
        server_socket.close()


if __name__ == "__main__":
    main()
