import socket
import threading
import sys
import argparse

# Tamanho do buffer para receber mensagens
BUFFER_SIZE = 1024

# Evento usado para sinalizar encerramento entre threads
shutdown_event = threading.Event()


def receive_messages(sock):
    """
    Função que roda em uma thread separada para receber mensagens do servidor.
    Quando o servidor fecha a conexão, a thread encerra o programa.
    """
    while not shutdown_event.is_set():
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                # Se não houver dados, o servidor provavelmente fechou a conexão
                print("\nConexão com o servidor encerrada.")
                shutdown_event.set()
                break

            # Exibe a mensagem recebida
            print(data.decode('utf-8'), end='')

        except socket.error:
            # Erro de conexão ou interrupção da rede
            if not shutdown_event.is_set():
                print("\nErro ao receber mensagem do servidor.")
                shutdown_event.set()
            break


def validate_whisper_command(message):
    """
    Valida se o comando /whisper está bem formatado.
    Retorna True se válido, False caso contrário.
    """
    parts = message.strip().split(' ', 2)
    return len(parts) == 3 and parts[0] == '/whisper'


def main():
    # Argumentos opcionais para host e porta
    parser = argparse.ArgumentParser(description='Cliente de chat TCP')
    parser.add_argument('--host', default='127.0.0.1', help='Endereço IP do servidor')
    parser.add_argument('--port', type=int, default=65433, help='Porta do servidor')
    args = parser.parse_args()

    try:
        # Criação do socket TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Conecta ao servidor especificado
        s.connect((args.host, args.port))
        print(f"Conectado ao servidor de chat em {args.host}:{args.port}")

        # Inicia thread para receber mensagens do servidor
        receive_thread = threading.Thread(target=receive_messages, args=(s,))
        receive_thread.start()

        # Loop principal para enviar mensagens do usuário
        while not shutdown_event.is_set():
            try:
                message = input()

                if message == '/quit':
                    # Envia comando de saída ao servidor
                    s.send('/quit'.encode('utf-8'))
                    shutdown_event.set()
                    break

                # Validação local do comando /whisper
                elif message.startswith('/whisper'):
                    if not validate_whisper_command(message):
                        print("Uso correto: /whisper <usuario> <mensagem>")
                        continue

                # Envia a mensagem ao servidor
                s.send(message.encode('utf-8'))

            except KeyboardInterrupt:
                # Permite o encerramento com Ctrl+C
                print("\nEncerrando cliente...")
                s.send('/quit'.encode('utf-8'))
                shutdown_event.set()
                break

            except Exception as e:
                # Captura erros inesperados e tenta fechar o cliente com segurança
                print(f"Erro ao enviar mensagem: {e}")
                shutdown_event.set()
                break

        # Aguarda a thread de recepção encerrar antes de sair
        receive_thread.join(timeout=2)
        s.close()

    except ConnectionRefusedError:
        print("Erro: Não foi possível conectar ao servidor. Verifique se ele está ativo.")
    except KeyboardInterrupt:
        print("\nCliente encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    main()
