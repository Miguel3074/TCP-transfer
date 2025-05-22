import socket
import threading
import os
import hashlib

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 12345

clientes = []
lock = threading.Lock()

def calcular_sha256(caminho_arquivo):
    hasher = hashlib.sha256()
    with open(caminho_arquivo, 'rb') as arquivo:
        while bloco := arquivo.read(4096):
            hasher.update(bloco)
    return hasher.hexdigest()

def enviar_para_todos(mensagem, remetente):
    with lock:
        for cliente in clientes:
            try:
                cliente.sendall(f"CHAT [{remetente[0]}:{remetente[1]}]: {mensagem}\n".encode('utf-8'))
            except:
                # Remove cliente se a conexão caiu
                with lock:
                    if cliente in clientes:
                        clientes.remove(cliente)

def lidar_com_cliente(conexao, endereco):
    print(f"Conexão aceita de {endereco}")
    with lock:
        clientes.append(conexao)
    try:
        while True:
            mensagem = conexao.recv(1024).decode('utf-8').strip()
            if not mensagem:
                break

            partes = mensagem.split(' ', 1)
            comando = partes[0].upper()
            argumento = partes[1] if len(partes) > 1 else ''

            if comando == 'SAIR':
                print(f"Cliente {endereco} solicitou sair.")
                with lock:
                    if conexao in clientes:
                        clientes.remove(conexao)
                conexao.close()
                break
            elif comando == 'ARQUIVO':
                nome_arquivo = argumento
                caminho_arquivo = os.path.join('.', nome_arquivo)
                if os.path.exists(caminho_arquivo):
                    try:
                        sha256_arquivo = calcular_sha256(caminho_arquivo)
                        tamanho_arquivo = os.path.getsize(caminho_arquivo)
                        conexao.sendall(f"OK\n{nome_arquivo}\n{tamanho_arquivo}\n{sha256_arquivo}\n\n".encode('utf-8'))
                        with open(caminho_arquivo, 'rb') as arquivo:
                            while bloco := arquivo.read(4096):
                                conexao.sendall(bloco)
                        print(f"Arquivo '{nome_arquivo}' enviado para {endereco}")
                    except Exception as e:
                        conexao.sendall(f"ERRO_AO_ENVIAR\n{e}\n\n".encode('utf-8'))
                else:
                    conexao.sendall("ERRO_ARQUIVO_NAO_ENCONTRADO\n\n".encode('utf-8'))
            elif comando == 'CHAT':
                print(f"[{endereco}] Chat: {argumento}")
                enviar_para_todos(argumento, endereco)
            else:
                conexao.sendall("COMANDO_DESCONHECIDO\n".encode('utf-8'))

    except Exception as e:
        print(f"Erro na comunicação com {endereco}: {e}")
    finally:
        with lock:
            if conexao in clientes:
                clientes.remove(conexao)
        conexao.close()
        print(f"Conexão com {endereco} encerrada.")

def iniciar_servidor():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        servidor_socket.bind((SERVER_HOST, SERVER_PORT))
        servidor_socket.listen()
        print(f"Servidor ouvindo em {SERVER_HOST}:{SERVER_PORT}")

        while True:
            conexao_cliente, endereco_cliente = servidor_socket.accept()
            thread_cliente = threading.Thread(target=lidar_com_cliente, args=(conexao_cliente, endereco_cliente))
            thread_cliente.daemon = True
            thread_cliente.start()
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
    finally:
        servidor_socket.close()

if __name__ == "__main__":
    iniciar_servidor()