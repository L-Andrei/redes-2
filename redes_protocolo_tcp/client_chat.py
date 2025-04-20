import socket
import threading
import sys
import argparse
import time

# Tamanho do buffer para receber mensagens
BUFFER_SIZE = 1024

# Evento usado para sinalizar encerramento entre threads
shutdown_event = threading.Event()

# Tempo máximo sem resposta antes de considerar desconectado
SOCKET_TIMEOUT = 15

def receive_messages(sock):
    """
    Thread que recebe mensagens do servidor.
    Se o servidor parar de responder, detecta a desconexão.
    """
    while not shutdown_event.is_set():
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print("\n[AVISO] Conexão encerrada pelo servidor.")
                shutdown_event.set()
                break
            print(data.decode('utf-8'), end='')

        except socket.timeout:
            print("\n[ERRO] Timeout: servidor não respondeu.")
            shutdown_event.set()
            break
        except (ConnectionResetError, BrokenPipeError):
            print("\n[ERRO] Conexão perdida com o servidor.")
            shutdown_event.set()
            break
        except Exception as e:
            print(f"\n[ERRO] Falha ao receber dados: {e}")
            shutdown_event.set()
            break


def send_heartbeat(sock):
    """
    Thread que envia um 'ping' periódico ao servidor para manter a conexão ativa
    e detectar falhas silenciosas.
    """
    while not shutdown_event.is_set():
        try:
            time.sleep(SOCKET_TIMEOUT // 2)
            # Envia um comando de ping (o servidor pode ignorar ou responder)
            sock.send(b"/ping\n")
        except Exception:
            print("\n[ERRO] Falha ao enviar heartbeat.")
            shutdown_event.set()
            break


def validate_whisper_command(message):
    """Verifica se o comando /whisper tem formato válido"""
    parts = message.strip().split(' ', 2)
    return len(parts) == 3 and parts[0] == '/whisper'


def main():
    parser = argparse.ArgumentParser(description='Cliente de chat TCP')
    parser.add_argument('--host', default='127.0.0.1', help='IP do servidor')
    parser.add_argument('--port', type=int, default=65433, help='Porta do servidor')
    args = parser.parse_args()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SOCKET_TIMEOUT)
        s.connect((args.host, args.port))
        print(f"[INFO] Conectado a {args.host}:{args.port}")

        # Thread para receber mensagens
        receive_thread = threading.Thread(target=receive_messages, args=(s,))
        receive_thread.start()

        # Thread de heartbeat para manter a conexão ativa
        heartbeat_thread = threading.Thread(target=send_heartbeat, args=(s,))
        heartbeat_thread.start()

        # Loop principal para leitura de comandos/mensagens
        while not shutdown_event.is_set():
            try:
                message = input()

                if message == '/quit':
                    s.send(b'/quit')
                    shutdown_event.set()
                    break

                elif message.startswith('/whisper'):
                    if not validate_whisper_command(message):
                        print("[USO] /whisper <usuario> <mensagem>")
                        continue

                s.send(message.encode('utf-8'))

            except KeyboardInterrupt:
                print("\n[INFO] Encerrando cliente...")
                try:
                    s.send(b'/quit')
                except:
                    pass
                shutdown_event.set()
                break
            except BrokenPipeError:
                print("\n[ERRO] Conexão encerrada.")
                shutdown_event.set()
                break
            except Exception as e:
                print(f"[ERRO] Falha ao enviar: {e}")
                shutdown_event.set()
                break

        # Finaliza conexões e threads
        receive_thread.join(timeout=2)
        heartbeat_thread.join(timeout=2)
        s.close()

    except ConnectionRefusedError:
        print("[ERRO] Não foi possível conectar ao servidor.")
    except Exception as e:
        print(f"[ERRO] {e}")


if __name__ == "__main__":
    main()
