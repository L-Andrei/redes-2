import socket
import time
import random
import sys


def test_connection_refused():
    """Testa comportamento quando o servidor está indisponível"""
    print("Teste 1: Conexão recusada")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Tentativa de conexão a um servidor inexistente
        s.connect(('127.0.0.1', 9999))
        print("FALHA: Não deveria conseguir conectar")
    except ConnectionRefusedError:
        print("SUCESSO: Conexão recusada detectada corretamente")
    except Exception as e:
        print(f"FALHA: Exceção inesperada: {e}")
    finally:
        s.close()


def test_sudden_disconnect(host, port):
    """Testa comportamento quando a conexão é interrompida abruptamente"""
    print("\nTeste 2: Desconexão súbita")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        print("Conectado ao servidor")
        # Envia mensagem de teste
        s.sendall("Teste de mensagem".encode('utf-8'))
        # Fecha o socket abruptamente
        s.close()
        print("SUCESSO: Socket fechado abruptamente")
    except Exception as e:
        print(f"FALHA: Exceção inesperada: {e}")


def test_malformed_data(host, port):
    """Testa comportamento quando dados malformados são enviados"""
    print("\nTeste 3: Dados malformados")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        print("Conectado ao servidor")
        # Envia bytes aleatórios
        s.sendall(bytes([random.randint(0, 255) for _ in range(100)]))
        # Recebe resposta se houver
        try:
            s.settimeout(2)
            response = s.recv(1024)
            print(f"Resposta recebida: {response}")
        except socket.timeout:
            print("Timeout na resposta (pode ser normal)")
        s.close()
        print("SUCESSO: Teste de dados malformados concluído")
    except Exception as e:
        print(f"FALHA: Exceção inesperada: {e}")
        s.close()


def main():
    if len(sys.argv) != 3:
        print(f"Uso: {sys.argv[0]} <host> <porta>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    test_connection_refused()
    test_sudden_disconnect(host, port)
    test_malformed_data(host, port)


if __name__ == "__main__":
    main()
