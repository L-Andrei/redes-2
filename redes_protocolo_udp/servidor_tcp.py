import socket
import os
import threading
import sys
import time

class ServidorTCP:
    def __init__(self):
        # Server configuration
        self.HOST = '0.0.0.0'
        self.PORT = 9700
        self.BUFFER_SIZE = 4096
        self.DIRETORIO_ARQUIVOS = './arquivos_tcp_recebidos/'
        
        # Create directory if it doesn't exist
        os.makedirs(self.DIRETORIO_ARQUIVOS, exist_ok=True)
        
        # Initialize TCP socket
        self.inicializar_servidor()

    def inicializar_servidor(self):
        """Initialize and configure the TCP server socket"""
        try:
            self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.servidor.bind((self.HOST, self.PORT))
            self.servidor.listen(5)
            print(f"Servidor TCP iniciado em {self.HOST}:{self.PORT}")
        except socket.error as e:
            print(f"Erro ao criar socket: {e}")
            sys.exit(1)

    def handle_client(self, conn, addr):
        """Handle client connection and file transfer"""
        print(f"\nNova conexão: {addr}")
        try:
            # Receive filename
            nome_arquivo = conn.recv(self.BUFFER_SIZE).decode('utf-8')
            if not nome_arquivo:
                return

            # Prepare file path
            caminho_arquivo = os.path.join(self.DIRETORIO_ARQUIVOS, nome_arquivo)
            
            # Send ready confirmation
            conn.send("PRONTO".encode('utf-8'))

            # Receive and save file
            with open(caminho_arquivo, 'wb') as f:
                bytes_recebidos = 0
                inicio = time.time()
                
                while True:
                    dados = conn.recv(self.BUFFER_SIZE)
                    if not dados or dados == b'FIM':
                        break
                    f.write(dados)
                    bytes_recebidos += len(dados)
                
                fim = time.time()
                self.mostrar_estatisticas(nome_arquivo, bytes_recebidos, inicio, fim)

        except Exception as e:
            print(f"Erro no processamento do cliente {addr}: {e}")
        finally:
            conn.close()
            print(f"Conexão fechada: {addr}")

    def mostrar_estatisticas(self, nome_arquivo, bytes_recebidos, inicio, fim):
        """Show transfer statistics"""
        tempo_total = fim - inicio
        taxa = bytes_recebidos / tempo_total / 1024  # KB/s
        
        print("\n" + "="*50)
        print(f"Arquivo recebido: {nome_arquivo}")
        print(f"Tamanho: {bytes_recebidos/1024:.2f} KB")
        print(f"Tempo total: {tempo_total:.2f} segundos")
        print(f"Taxa de transferência: {taxa:.2f} KB/s")
        print("="*50)

    def iniciar(self):
        """Start the server main loop"""
        try:
            print("Aguardando conexões...")
            while True:
                conn, addr = self.servidor.accept()
                thread_cliente = threading.Thread(
                    target=self.handle_client,
                    args=(conn, addr)
                )
                thread_cliente.daemon = True
                thread_cliente.start()
                
        except KeyboardInterrupt:
            print("\nServidor encerrado pelo usuário.")
        finally:
            self.servidor.close()
            print("Socket do servidor fechado.")

if __name__ == "__main__":
    servidor = ServidorTCP()
    servidor.iniciar()