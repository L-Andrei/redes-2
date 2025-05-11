import socket
import threading
import time
import sys
from datetime import datetime

# ==============================================
# CONFIGURAÇÕES DO SERVIDOR
# ==============================================
HOST = '0.0.0.0'  # Aceita conexões de qualquer interface de rede
PORT = 9500       # Porta padrão para o servidor escutar
BUFFER_SIZE = 1024  # Tamanho máximo do buffer para mensagens

# Dicionário para armazenar os clientes conectados no formato {endereço: nome}
clientes = {}

# ==============================================
# INICIALIZAÇÃO DO SOCKET UDP
# ==============================================
try:
    # Cria socket UDP (SOCK_DGRAM)
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Associa o socket ao endereço e porta especificados
    servidor.bind((HOST, PORT))
    print(f"Servidor iniciado em {HOST}:{PORT}")
except socket.error as e:
    print(f"Erro ao criar socket: {e}")
    sys.exit(1)  # Encerra o programa em caso de erro

# ==============================================
# FUNÇÕES AUXILIARES
# ==============================================

def get_timestamp():
    """Retorna a hora atual formatada como string no formato HH:MM:SS"""
    return datetime.now().strftime("%H:%M:%S")

def broadcast(mensagem, endereco_origem=None):
    """
    Envia uma mensagem para todos os clientes conectados, exceto o remetente original
    
    Parâmetros:
        mensagem (str): Mensagem a ser enviada
        endereco_origem (tuple): Endereço (IP, porta) do remetente que não receberá a mensagem
    """
    for endereco in clientes:
        # Não envia de volta para o remetente original
        if endereco != endereco_origem:
            try:
                # Codifica a mensagem para bytes e envia para o cliente
                servidor.sendto(mensagem.encode('utf-8'), endereco)
            except Exception as e:
                # Se houver erro no envio, remove o cliente inacessível
                print(f"Erro ao enviar mensagem para {endereco}: {e}")
                nome = clientes.pop(endereco, "Unknown")
                # Notifica outros clientes sobre a desconexão
                broadcast(f"[{get_timestamp()}] {nome} saiu do chat (conexão perdida).", endereco)

def send_private_message(remetente_endereco, comando):
    """
    Processa e envia mensagens privadas entre usuários
    
    Parâmetros:
        remetente_endereco (tuple): Endereço do cliente que está enviando a mensagem privada
        comando (str): Comando completo no formato "/pm destinatario mensagem"
    """
    try:
        # Divide o comando em partes: ["/pm", "destinatario", "mensagem"]
        partes = comando.split(' ', 2)
        
        # Verifica se o comando está completo
        if len(partes) < 3:
            msg_erro = f"[{get_timestamp()}] Uso correto: /pm usuário mensagem"
            servidor.sendto(msg_erro.encode('utf-8'), remetente_endereco)
            return
        
        destinatario_nome = partes[1]  # Nome do destinatário
        mensagem = partes[2]           # Conteúdo da mensagem
        remetente_nome = clientes.get(remetente_endereco, "Unknown")  # Nome do remetente
        
        # Procura o endereço do destinatário na lista de clientes
        destinatario_endereco = None
        for endereco, nome in clientes.items():
            if nome.lower() == destinatario_nome.lower():
                destinatario_endereco = endereco
                break
        
        if destinatario_endereco:
            # Formata a mensagem para o destinatário
            msg_privada = f"[{get_timestamp()}] [PRIVADO] {remetente_nome} para você: {mensagem}"
            servidor.sendto(msg_privada.encode('utf-8'), destinatario_endereco)
            
            # Envia confirmação para o remetente
            confirmacao = f"[{get_timestamp()}] [PRIVADO] Mensagem enviada para {destinatario_nome}: {mensagem}"
            servidor.sendto(confirmacao.encode('utf-8'), remetente_endereco)
        else:
            # Destinatário não encontrado
            msg_erro = f"[{get_timestamp()}] Usuário '{destinatario_nome}' não encontrado ou offline."
            servidor.sendto(msg_erro.encode('utf-8'), remetente_endereco)
            
    except Exception as e:
        print(f"Erro ao processar mensagem privada: {e}")
        servidor.sendto(f"[{get_timestamp()}] Erro ao enviar mensagem privada.".encode('utf-8'), remetente_endereco)

# ==============================================
# LOOP PRINCIPAL DO SERVIDOR
# ==============================================
try:
    print("Aguardando mensagens...")
    while True:
        try:
            # Recebe dados do cliente (bloqueante)
            dados, endereco = servidor.recvfrom(BUFFER_SIZE)
            mensagem = dados.decode('utf-8').strip()

            # ==================================
            # PROCESSAMENTO DE COMANDOS
            # ==================================
            
            # Comando: /registro:nome
            if mensagem.startswith('/registro:'):
                # Extrai o nome do cliente (remove '/registro:')
                nome = mensagem.split(':')[1].strip()
                
                # Validação do nome
                if not nome:
                    servidor.sendto(f"[{get_timestamp()}] Nome inválido. Por favor, use /registro:seunome".encode('utf-8'), endereco)
                    continue
                
                # Adiciona cliente ao dicionário
                clientes[endereco] = nome
                print(f"[{get_timestamp()}] {nome} conectado de {endereco}")
                
                # Confirmação para o cliente
                servidor.sendto(f"[{get_timestamp()}] Registro bem-sucedido como {nome}".encode('utf-8'), endereco)
                
                # Notifica outros clientes sobre a nova conexão
                broadcast(f"[{get_timestamp()}] {nome} entrou no chat!", endereco)

            # Comando: /sair
            elif mensagem.startswith('/sair'):
                if endereco in clientes:
                    nome = clientes[endereco]
                    # Remove cliente da lista
                    del clientes[endereco]
                    print(f"[{get_timestamp()}] {nome} desconectado de {endereco}")
                    
                    # Notifica outros clientes sobre a saída
                    broadcast(f"[{get_timestamp()}] {nome} saiu do chat.", endereco)
                    
                    # Confirmação para o cliente que está saindo
                    servidor.sendto(f"[{get_timestamp()}] Desconectado com sucesso.".encode('utf-8'), endereco)

            # Comando: /pm (mensagem privada)
            elif mensagem.startswith('/pm '):
                if endereco in clientes:
                    send_private_message(endereco, mensagem)
                else:
                    # Cliente não registrado tentando enviar mensagem privada
                    servidor.sendto(f"[{get_timestamp()}] Por favor, registre-se primeiro com /registro:seunome".encode('utf-8'), endereco)

            # Mensagem normal (broadcast)
            else:
                if endereco in clientes:
                    nome = clientes[endereco]
                    # Formata mensagem com timestamp e nome do remetente
                    mensagem_formatada = f"[{get_timestamp()}] {nome}: {mensagem}"
                    print(mensagem_formatada)
                    # Envia para todos os clientes (exceto o remetente)
                    broadcast(mensagem_formatada, endereco)
                else:
                    # Cliente não registrado tentando enviar mensagem
                    servidor.sendto(f"[{get_timestamp()}] Por favor, registre-se primeiro com /registro:seunome".encode('utf-8'), endereco)

        except Exception as e:
            print(f"[{get_timestamp()}] Erro no processamento da mensagem: {e}")

except KeyboardInterrupt:
    # Trata interrupção por teclado (Ctrl+C)
    print(f"\n[{get_timestamp()}] Servidor encerrado pelo usuário.")
finally:
    # ==============================================
    # ROTINA DE ENCERRAMENTO
    # ==============================================
    
    # Notifica todos os clientes sobre o encerramento do servidor
    for endereco in list(clientes.keys()):
        servidor.sendto(f"[{get_timestamp()}] O servidor está sendo encerrado. Conexão finalizada.".encode('utf-8'), endereco)
    
    # Fecha o socket do servidor
    servidor.close()
    print(f"[{get_timestamp()}] Socket do servidor fechado.")