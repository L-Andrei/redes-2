import socket
import os
import sys
import time
import math

# Configurações do cliente
SERVIDOR_HOST = 'localhost'
SERVIDOR_PORT = 9600
BUFFER_SIZE = 4096
TAMANHO_FRAGMENTO = 1024  # Tamanho de cada fragmento a ser enviado
TIMEOUT = 1.0            # Timeout para retransmissão em segundos
MAX_TENTATIVAS = 10       # Número máximo de tentativas de retransmissão

# Criar socket UDP
try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cliente.settimeout(TIMEOUT)
except socket.error as e:
    print(f"Erro ao criar socket: {e}")
    sys.exit(1)

def enviar_arquivo(caminho_arquivo):
    """
    Envia um arquivo fragmentado para o servidor com mecanismo de confirmação (ACKs),
    timeout e retransmissão. Mostra o progresso e estatísticas da transferência.
    
    Args:
        caminho_arquivo (str): Caminho do arquivo a ser enviado
    """
    try:
        # Obter informações do arquivo
        nome_arquivo = os.path.basename(caminho_arquivo)
        tamanho_arquivo = os.path.getsize(caminho_arquivo)
        total_fragmentos = math.ceil(tamanho_arquivo / TAMANHO_FRAGMENTO)
        
        # Inicializar estatísticas
        inicio = time.time()
        retransmissoes = 0
        fragmentos_enviados = 0
        
        print(f"Enviando arquivo '{nome_arquivo}' ({tamanho_arquivo} bytes, {total_fragmentos} fragmentos)...")
        
        # Abrir arquivo para leitura em modo binário
        with open(caminho_arquivo, 'rb') as arquivo:
            # Enviar cada fragmento com controle de sequência
            for seq in range(total_fragmentos):
                # Ler fragmento do arquivo
                arquivo.seek(seq * TAMANHO_FRAGMENTO)
                dados = arquivo.read(TAMANHO_FRAGMENTO)
                
                # Criar pacote com cabeçalho de sequência
                cabecalho = f"{seq:05d}{total_fragmentos:05d}".encode('utf-8')
                pacote = cabecalho + dados
                
                tentativas = 0
                ack_recebido = False
                
                # Tentar enviar até receber ACK ou atingir máximo de tentativas
                while not ack_recebido and tentativas < MAX_TENTATIVAS:
                    try:
                        # Enviar fragmento
                        cliente.sendto(pacote, (SERVIDOR_HOST, SERVIDOR_PORT))
                        fragmentos_enviados += 1
                        
                        # Esperar por ACK
                        resposta, _ = cliente.recvfrom(BUFFER_SIZE)
                        
                        # Verificar se é o ACK esperado
                        if resposta.decode('utf-8') == f"ACK:{seq}":
                            ack_recebido = True
                            # Mostrar progresso
                            progresso = (seq + 1) / total_fragmentos * 100
                            print(f"\rProgresso: {progresso:.1f}% ({seq + 1}/{total_fragmentos})", end='')
                        else:
                            # Resposta inesperada, tratar como não-ACK
                            raise socket.timeout
                            
                    except socket.timeout:
                        tentativas += 1
                        retransmissoes += 1
                        if tentativas < MAX_TENTATIVAS:
                            print(f"\nTimeout fragmento {seq}, tentativa {tentativas + 1}...")
                        else:
                            print(f"\nFalha ao enviar fragmento {seq} após {MAX_TENTATIVAS} tentativas. Abortando.")
                            return
                
        # Calcular estatísticas finais
        tempo_total = time.time() - inicio
        taxa_transferencia = (tamanho_arquivo / 1024) / tempo_total if tempo_total > 0 else 0
        
        # Mostrar resumo da transferência
        print("\nTransferência concluída com sucesso!")
        print("=" * 50)
        print(f"{'Tempo (s)':<15} | {'Taxa (KB/s)':<15} | {'Retransmissões':<15}")
        print(f"{tempo_total:<15.2f} | {taxa_transferencia:<15.2f} | {retransmissoes:<15}")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nErro durante o envio do arquivo: {e}")
        return

def main():
    """
    Função principal que gerencia a execução do cliente.
    """
    if len(sys.argv) != 2:
        print("Uso: python cliente_arquivos.py <caminho_do_arquivo>")
        sys.exit(1)
        
    caminho_arquivo = sys.argv[1]
    
    # Verificar se o arquivo existe
    if not os.path.isfile(caminho_arquivo):
        print(f"Erro: O arquivo '{caminho_arquivo}' não existe.")
        sys.exit(1)
        
    try:
        # Enviar solicitação inicial ao servidor
        nome_arquivo = os.path.basename(caminho_arquivo)
        solicitacao = f"ENVIAR:{nome_arquivo}"
        print(f"Solicitando envio de '{nome_arquivo}' para o servidor...")
        
        cliente.sendto(solicitacao.encode('utf-8'), (SERVIDOR_HOST, SERVIDOR_PORT))
        
        # Esperar confirmação do servidor
        cliente.settimeout(5.0)  # 5 segundos para timeout inicial
        try:
            resposta, _ = cliente.recvfrom(BUFFER_SIZE)
            if resposta.decode('utf-8') == "PRONTO":
                print("Servidor pronto para receber. Iniciando envio...")
                enviar_arquivo(caminho_arquivo)
            else:
                print(f"Resposta inesperada do servidor: {resposta.decode('utf-8')}")
        except socket.timeout:
            print("Timeout: O servidor não respondeu à solicitação inicial.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nCliente encerrado pelo usuário.")
    finally:
        cliente.close()
        print("Socket do cliente fechado.")

if __name__ == "__main__":
    main()