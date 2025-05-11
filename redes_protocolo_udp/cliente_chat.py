import socket
import threading
import sys
import time
from datetime import datetime

# ==============================================
# CONFIGURAÇÕES DO CLIENTE
# ==============================================
SERVIDOR_HOST = 'localhost'  # Endereço do servidor
SERVIDOR_PORT = 9500         # Porta do servidor
BUFFER_SIZE = 1024           # Tamanho máximo do buffer

# ==============================================
# INICIALIZAÇÃO DO SOCKET UDP
# ==============================================
try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Define timeout para evitar bloqueio permanente
    cliente.settimeout(1.0)
except socket.error as e:
    print(f"Erro ao criar socket: {e}")
    sys.exit(1)

# Variável global para controle de execução
executando = True

# ==============================================
# FUNÇÕES AUXILIARES
# ==============================================

def get_timestamp():
    """Retorna a hora atual formatada como string no formato HH:MM:SS"""
    return datetime.now().strftime("%H:%M:%S")

def receber_mensagens():
    """
    Função executada em thread separada para receber mensagens do servidor continuamente.
    Imprime as mensagens recebidas no console.
    """
    global executando
    while executando:
        try:
            # Recebe dados do servidor
            dados, _ = cliente.recvfrom(BUFFER_SIZE)
            mensagem = dados.decode('utf-8')
            
            # Imprime a mensagem formatada
            print(f"\n{mensagem}\nDigite sua mensagem (/sair para sair): ", end="")
            
        except socket.timeout:
            # Timeout é esperado para verificar se ainda está executando
            continue
        except Exception as e:
            print(f"\nErro ao receber mensagem: {e}")
            executando = False
            break

def registrar_usuario(nome):
    """
    Envia comando de registro ao servidor e verifica a resposta.
    
    Parâmetros:
        nome (str): Nome de usuário para registro
        
    Retorna:
        bool: True se registro foi bem-sucedido, False caso contrário
    """
    try:
        # Envia comando de registro
        comando = f"/registro:{nome}"
        cliente.sendto(comando.encode('utf-8'), (SERVIDOR_HOST, SERVIDOR_PORT))
        
        # Aguarda confirmação
        dados, _ = cliente.recvfrom(BUFFER_SIZE)
        resposta = dados.decode('utf-8')
        
        print(f"[{get_timestamp()}] {resposta}")
        return True
        
    except Exception as e:
        print(f"[{get_timestamp()}] Erro ao registrar usuário: {e}")
        return False

def enviar_mensagem(mensagem):
    """
    Envia mensagem para o servidor.
    
    Parâmetros:
        mensagem (str): Mensagem a ser enviada
    """
    try:
        cliente.sendto(mensagem.encode('utf-8'), (SERVIDOR_HOST, SERVIDOR_PORT))
    except Exception as e:
        print(f"[{get_timestamp()}] Erro ao enviar mensagem: {e}")

# ==============================================
# FUNÇÃO PRINCIPAL
# ==============================================
def main():
    global executando
    
    # Verifica argumentos da linha de comando
    if len(sys.argv) != 2:
        print("Uso: python cliente_chat.py <seu_nome>")
        sys.exit(1)
    
    nome_usuario = sys.argv[1]
    
    try:
        # Registrar no servidor
        if not registrar_usuario(nome_usuario):
            print("[{get_timestamp()}] Falha no registro. Encerrando cliente.")
            return
        
        # Iniciar thread para receber mensagens
        thread_recebimento = threading.Thread(target=receber_mensagens)
        thread_recebimento.daemon = True
        thread_recebimento.start()
        
        print(f"[{get_timestamp()}] Conectado ao servidor. Digite sua mensagem ou '/sair' para encerrar.")
        
        # Loop principal para enviar mensagens
        while executando:
            try:
                # Lê entrada do usuário
                mensagem = input("Digite sua mensagem (/sair para sair): ")
                
                if mensagem.lower() == '/sair':
                    # Envia comando de saída
                    enviar_mensagem("/sair")
                    executando = False
                    break
                
                # Envia mensagem normal
                enviar_mensagem(mensagem)
                
            except KeyboardInterrupt:
                print("\n[{get_timestamp()}] Encerrando cliente...")
                enviar_mensagem("/sair")
                executando = False
                break
            except Exception as e:
                print(f"\n[{get_timestamp()}] Erro: {e}")
                executando = False
                break
                
    except Exception as e:
        print(f"[{get_timestamp()}] Erro fatal: {e}")
    finally:
        # Garante que o socket seja fechado corretamente
        executando = False
        cliente.close()
        print(f"[{get_timestamp()}] Socket do cliente fechado.")

if __name__ == "__main__":
    main()