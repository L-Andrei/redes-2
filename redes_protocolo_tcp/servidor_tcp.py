import socket
from datetime import datetime

# Configurações do servidor
HOST = '127.0.0.1'  # Endereço de loopback (localhost)
PORT = 65432        # Porta para escutar (não privilegiada)

try:
    # Criação do socket TCP/IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Servidor escutando em {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"\nConectado por {addr}")
                inicio_conexao = datetime.now()

                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] Mensagem de {addr}: {data.decode('utf-8')}")
                    conn.sendall(f"Eco: {data.decode('utf-8')}".encode('utf-8'))

                fim_conexao = datetime.now()
                duracao = fim_conexao - inicio_conexao
                print(f"Conexão com {addr} encerrada. Duração: {duracao}")
except KeyboardInterrupt:
    print("\nServidor encerrado pelo usuário")
except Exception as e:
    print(f"Erro: {e}")
