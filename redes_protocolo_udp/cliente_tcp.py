import socket
import os
import sys
import time

class ClienteTCP:
    def __init__(self):
        # Client configuration
        self.SERVIDOR_HOST = 'localhost'
        self.SERVIDOR_PORT = 9700
        self.BUFFER_SIZE = 4096

    def enviar_arquivo(self, caminho_arquivo, conn):
        """Send file to server with progress tracking"""
        try:
            # Get file info
            tamanho_arquivo = os.path.getsize(caminho_arquivo)
            nome_arquivo = os.path.basename(caminho_arquivo)
            
            # Send filename
            conn.send(nome_arquivo.encode('utf-8'))
            
            # Wait for server confirmation
            confirmacao = conn.recv(self.BUFFER_SIZE).decode('utf-8')
            if confirmacao != "PRONTO":
                print(f"Erro: Resposta inesperada do servidor: {confirmacao}")
                return False

            # Send file data
            with open(caminho_arquivo, 'rb') as f:
                bytes_enviados = 0
                inicio = time.time()
                
                while True:
                    dados = f.read(self.BUFFER_SIZE)
                    if not dados:
                        break
                    
                    conn.send(dados)
                    bytes_enviados += len(dados)
                    self.mostrar_progresso(bytes_enviados, tamanho_arquivo)

                # Send end marker
                conn.send(b'FIM')
                fim = time.time()
                self.mostrar_estatisticas(bytes_enviados, inicio, fim)
                return True

        except Exception as e:
            print(f"Erro ao enviar arquivo: {e}")
            return False

    def mostrar_progresso(self, enviados, total):
        """Show transfer progress"""
        progresso = enviados / total * 100
        print(f"\rEnviando... {progresso:.1f}% ({enviados}/{total} bytes)", end="")

    def mostrar_estatisticas(self, bytes_enviados, inicio, fim):
        """Show transfer statistics"""
        tempo_total = fim - inicio
        taxa = bytes_enviados / tempo_total / 1024  # KB/s
        
        print("\n" + "="*50)
        print("Transferência concluída com sucesso!")
        print(f"Tamanho enviado: {bytes_enviados/1024:.2f} KB")
        print(f"Tempo total: {tempo_total:.2f} segundos")
        print(f"Taxa de transferência: {taxa:.2f} KB/s")
        print("="*50)

    def iniciar(self, caminho_arquivo):
        """Start the client connection"""
        # Verify file exists
        if not os.path.isfile(caminho_arquivo):
            print(f"Erro: O arquivo '{caminho_arquivo}' não existe.")
            sys.exit(1)

        try:
            # Connect to server
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"\nConectando ao servidor {self.SERVIDOR_HOST}:{self.SERVIDOR_PORT}...")
            cliente.connect((self.SERVIDOR_HOST, self.SERVIDOR_PORT))
            
            # Start file transfer
            print(f"Enviando arquivo '{os.path.basename(caminho_arquivo)}'...")
            self.enviar_arquivo(caminho_arquivo, cliente)

        except ConnectionRefusedError:
            print("Conexão recusada. Verifique se o servidor está em execução.")
        except KeyboardInterrupt:
            print("\nCliente encerrado pelo usuário.")
        finally:
            cliente.close()
            print("Socket do cliente fechado.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python cliente_tcp.py <caminho_do_arquivo>")
        sys.exit(1)
    
    cliente = ClienteTCP()
    cliente.iniciar(sys.argv[1])