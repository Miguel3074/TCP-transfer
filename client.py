import socket
import hashlib

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345

def calcular_sha256(caminho_arquivo):
    hasher = hashlib.sha256()
    with open(caminho_arquivo, 'rb') as arquivo:
        while bloco := arquivo.read(4096):
            hasher.update(bloco)
    return hasher.hexdigest()

def receber_arquivo(conexao):
    resposta = conexao.recv(1024).decode('utf-8').strip().split('\n')
    status = resposta[0]
    if status == 'OK':
        nome_arquivo = resposta[1]
        tamanho_arquivo = int(resposta[2])
        hash_servidor = resposta[3]
        print(f"Recebendo arquivo '{nome_arquivo}' ({tamanho_arquivo} bytes)...")

        with open(f"recebido_{nome_arquivo}", 'wb') as arquivo_local:
            bytes_recebidos = 0
            while bytes_recebidos < tamanho_arquivo:
                bloco = conexao.recv(4096)
                if not bloco:
                    break
                arquivo_local.write(bloco)
                bytes_recebidos += len(bloco)
        print("Arquivo recebido.")

        hash_local = calcular_sha256(f"recebido_{nome_arquivo}")
        if hash_local == hash_servidor:
            print("Verificação de integridade: SUCESSO! Hashes coincidem.")
        else:
            print(f"Verificação de integridade: FALHA! Hashes diferentes (Servidor: {hash_servidor}, Local: {hash_local}).")
    elif status == 'ERRO_ARQUIVO_NAO_ENCONTRADO':
        print("Erro: Arquivo não encontrado no servidor.")
    elif status == 'ERRO_AO_ENVIAR':
        print(f"Erro ao receber o arquivo do servidor: {resposta[1]}")
    else:
        print(f"Resposta inesperada do servidor: {resposta}")

def iniciar_cliente():
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cliente_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Conectado ao servidor em {SERVER_IP}:{SERVER_PORT}")

        # thread_recebimento = threading.Thread(target=receber_mensagens, args=(cliente_socket,))
        # thread_recebimento.daemon = True
        # thread_recebimento.start()

        while True:
            comando = input("> ").strip()
            if comando.upper() == 'SAIR':
                cliente_socket.sendall("SAIR".encode('utf-8'))
                break
            elif comando.upper().startswith('ARQUIVO'):
                cliente_socket.sendall(comando.encode('utf-8'))
                receber_arquivo(cliente_socket)
            elif comando.upper().startswith('CHAT'):
                cliente_socket.sendall(comando.encode('utf-8'))
            else:
                print("Comando inválido.")

    except ConnectionRefusedError:
        print("Erro: Conexão recusada. Verifique se o servidor está rodando.")
    except Exception as e:
        print(f"Erro no cliente: {e}")
    finally:
        cliente_socket.close()

if __name__ == "__main__":
    iniciar_cliente()