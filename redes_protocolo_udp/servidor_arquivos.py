import socket
import os
import time
import sys
from collections import defaultdict

# Configurações do servidor
HOST = '0.0.0.0'
PORT = 9600
BUFFER_SIZE = 4096
DIRETORIO_ARQUIVOS = './arquivos_recebidos/'
TIMEOUT = 30  # Timeout para espera de fragmentos

# Criar diretório para salvar arquivos se não existir
os.makedirs(DIRETORIO_ARQUIVOS, exist_ok=True)

# Criar socket UDP
try:
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.bind((HOST, PORT))
    print(f"Servidor de arquivos iniciado em {HOST}:{PORT}")
except socket.error as e:
    print(f"Erro ao criar socket: {e}")
    sys.exit(1)

def receber_arquivo(nome_arquivo, endereco_cliente):
    """
    Recebe um arquivo fragmentado do cliente, envia ACKs para cada fragmento
    e salva o arquivo completo no diretório especificado.
    
    Args:
        nome_arquivo (str): Nome do arquivo a ser recebido
        endereco_cliente (tuple): Endereço do cliente (host, port)
    """
    try:
        caminho_completo = os.path.join(DIRETORIO_ARQUIVOS, nome_arquivo)
        fragmentos_recebidos = defaultdict(bytes)
        total_fragmentos = None
        ultimo_seq_recebido = -1
        inicio = time.time()
        
        print(f"Preparando para receber '{nome_arquivo}'...")
        
        with open(caminho_completo, 'wb') as arquivo:
            while True:
                try:
                    # Configurar timeout para recebimento
                    servidor.settimeout(TIMEOUT)
                    
                    # Receber pacote do cliente
                    dados, _ = servidor.recvfrom(BUFFER_SIZE)
                    
                    # Extrair cabeçalho (seq (5) + total (5) = 10 bytes)
                    cabecalho = dados[:10].decode('utf-8')
                    seq = int(cabecalho[:5])
                    total = int(cabecalho[5:10])
                    
                    # Se for o primeiro fragmento, inicializar total_fragmentos
                    if total_fragmentos is None:
                        total_fragmentos = total
                        print(f"Total de fragmentos esperados: {total_fragmentos}")
                    
                    # Verificar se é um fragmento novo
                    if seq not in fragmentos_recebidos:
                        fragmentos_recebidos[seq] = dados[10:]  # Armazenar dados sem cabeçalho
                        ultimo_seq_recebido = max(ultimo_seq_recebido, seq)
                        progresso = (len(fragmentos_recebidos) / total_fragmentos) * 100
                        print(f"\rProgresso: {progresso:.1f}% ({len(fragmentos_recebidos)}/{total_fragmentos})", end='')
                    
                    # Enviar ACK para o fragmento recebido
                    ack = f"ACK:{seq}".encode('utf-8')
                    servidor.sendto(ack, endereco_cliente)
                    
                    # Verificar se todos os fragmentos foram recebidos
                    if len(fragmentos_recebidos) == total_fragmentos:
                        print("\nTodos os fragmentos recebidos. Salvando arquivo...")
                        
                        # Escrever fragmentos em ordem no arquivo
                        for i in range(total_fragmentos):
                            arquivo.write(fragmentos_recebidos[i])
                        
                        # Calcular estatísticas
                        tempo_total = time.time() - inicio
                        tamanho_arquivo = os.path.getsize(caminho_completo)
                        taxa_transferencia = (tamanho_arquivo / 1024) / tempo_total if tempo_total > 0 else 0
                        
                        print(f"Arquivo salvo em: {caminho_completo}")
                        print(f"Tamanho: {tamanho_arquivo} bytes")
                        print(f"Tempo total: {tempo_total:.2f} segundos")
                        print(f"Taxa de transferência: {taxa_transferencia:.2f} KB/s")
                        return
                        
                except socket.timeout:
                    print(f"\nTimeout ao esperar fragmentos. Fragmentos recebidos: {len(fragmentos_recebidos)}/{total_fragmentos}")
                    return
                except Exception as e:
                    print(f"\nErro ao receber arquivo: {e}")
                    return
    
    except Exception as e:
        print(f"Erro durante o recebimento do arquivo: {e}")
        if os.path.exists(caminho_completo):
            os.remove(caminho_completo)

# Loop principal do servidor
try:
    print("Aguardando conexões...")
    while True:
        try:
            # Receber solicitação inicial
            dados, endereco = servidor.recvfrom(BUFFER_SIZE)
            mensagem = dados.decode('utf-8')
            
            # Se for uma solicitação de envio de arquivo
            if mensagem.startswith('ENVIAR:'):
                nome_arquivo = mensagem.split(':')[1]
                print(f"\nSolicitação para receber arquivo: {nome_arquivo} de {endereco}")
                
                # Enviar confirmação de pronto para receber
                servidor.sendto("PRONTO".encode('utf-8'), endereco)
                
                # Receber o arquivo
                receber_arquivo(nome_arquivo, endereco)
                
        except Exception as e:
            print(f"Erro: {e}")
            
except KeyboardInterrupt:
    print("\nServidor encerrado pelo usuário.")
finally:
    servidor.close()
    print("Socket do servidor fechado.")
