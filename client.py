import socket
import hashlib
import threading
import os
import sys

SERVER_IP = '127.0.0.1' 
SERVER_PORT = 12345

def calcular_sha256(caminho_arquivo):
    hasher = hashlib.sha256()
    with open(caminho_arquivo, 'rb') as arquivo:
        while bloco := arquivo.read(4096):
            hasher.update(bloco)
    return hasher.hexdigest()

def receber_mensagens(sock):
    while True:
        try:
            resposta_inicial = sock.recv(1024).decode('utf-8')
            if not resposta_inicial:
                break

            linhas = resposta_inicial.strip().split('\n')
            comando_status = linhas[0]

            if comando_status == 'OK':
                nome_arquivo = linhas[1]
                tamanho_arquivo = int(linhas[2])
                hash_servidor = linhas[3]
                
                header_completo = resposta_inicial
                while '\n\n' not in header_completo:
                    header_completo += sock.recv(1024).decode('utf-8')
                
                _, corpo_inicial = header_completo.split('\n\n', 1)
                corpo_inicial_bytes = corpo_inicial.encode('utf-8')
                
                caminho_local = f"recebido_{nome_arquivo}"
                print(f"\nRecebendo '{nome_arquivo}' ({tamanho_arquivo} bytes)...")

                bytes_recebidos = 0
                with open(caminho_local, 'wb') as arquivo_local:
                    if corpo_inicial_bytes:
                        arquivo_local.write(corpo_inicial_bytes)
                        bytes_recebidos += len(corpo_inicial_bytes)
                    
                    while bytes_recebidos < tamanho_arquivo:
                        bloco = sock.recv(4096)
                        if not bloco:
                            break
                        arquivo_local.write(bloco)
                        bytes_recebidos += len(bloco)
                
                print("Arquivo recebido com sucesso.")

                hash_local = calcular_sha256(caminho_local)
                if hash_local == hash_servidor:
                    print("✅ Verificação de integridade: SUCESSO! Hashes coincidem.")
                else:
                    print(f"❌ Verificação de integridade: FALHA! Hashes diferentes.")
                    print(f"   - Servidor: {hash_servidor}")
                    print(f"   - Local:    {hash_local}")

            elif comando_status.startswith('CHAT'):
                sys.stdout.write(f"\r{linhas[0]}\n> ")
                sys.stdout.flush()
            elif comando_status == 'ERRO_ARQUIVO_NAO_ENCONTRADO':
                print("\nErro: Arquivo não encontrado no servidor.")
            else:
                sys.stdout.write(f"\r{resposta_inicial.strip()}\n> ")
                sys.stdout.flush()

        except ConnectionResetError:
            print("\nConexão com o servidor foi perdida.")
            break
        except Exception as e:
            print(f"\nErro ao receber dados: {e}")
            break
    os._exit(0)

def iniciar_cliente():
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cliente_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Conectado ao servidor em {SERVER_IP}:{SERVER_PORT}")
        print("Digite 'CHAT <mensagem>', 'ARQUIVO <nome_arquivo>' ou 'SAIR'.")
        print("> ", end="")
        
        thread_recebimento = threading.Thread(target=receber_mensagens, args=(cliente_socket,), daemon=True)
        thread_recebimento.start()

        while thread_recebimento.is_alive():
            try:
                comando = input()
                if comando:
                    cliente_socket.sendall(comando.encode('utf-8'))
                    if comando.upper() == 'SAIR':
                        break
                print("> ", end="")
            except (KeyboardInterrupt, EOFError):
                cliente_socket.sendall(b'SAIR')
                break

    except ConnectionRefusedError:
        print("Erro: Conexão recusada. Verifique se o servidor está rodando.")
    except Exception as e:
        print(f"Erro no cliente: {e}")
    finally:
        print("\nEncerrando cliente.")
        cliente_socket.close()

if __name__ == "__main__":
    iniciar_cliente()