import socket
import threading
import os
from datetime import datetime

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 12345

# Mapeamento de extensões de arquivo para tipos de conteúdo (MIME types)
MIME_TYPES = {
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'ico': 'image/x-icon',
}

def lidar_com_cliente(conexao, endereco):
    """Lida com uma única conexão de cliente (navegador)."""
    print(f"✅ Conexão aceita de {endereco}")
    
    try:
        # Recebe a requisição do navegador (até 4KB é suficiente para cabeçalhos)
        requisicao_bytes = conexao.recv(4096)
        if not requisicao_bytes:
            return

        requisicao_str = requisicao_bytes.decode('utf-8')
        
        # Pega a primeira linha da requisição (ex: "GET /index.html HTTP/1.1")
        primeira_linha = requisicao_str.split('\n')[0]
        print(f"-> Requisição de {endereco}: \"{primeira_linha.strip()}\"")
        
        # Extrai o método e o caminho do arquivo
        try:
            metodo, caminho, _ = primeira_linha.split()
        except ValueError:
            # Se a linha de requisição não estiver no formato esperado
            metodo, caminho = 'GET', '/' # Define um padrão ou trata como erro

        # Se o caminho for apenas "/", sirva o "index.html"
        if caminho == '/':
            caminho = '/index.html'

        # Monta o caminho completo para o arquivo local
        # Remove a barra inicial para concatenar com o diretório atual
        caminho_arquivo = os.path.join('.', caminho.lstrip('/'))

        # --- Verificação e Construção da Resposta ---

        if os.path.exists(caminho_arquivo) and os.path.isfile(caminho_arquivo):
            # Resposta 200 OK - Arquivo Encontrado
            
            # Pega a extensão do arquivo para determinar o Content-Type
            extensao = caminho_arquivo.split('.')[-1]
            tipo_conteudo = MIME_TYPES.get(extensao, 'application/octet-stream')
            
            # Lê o conteúdo do arquivo em modo binário ('rb')
            with open(caminho_arquivo, 'rb') as arquivo:
                corpo_resposta = arquivo.read()
            
            tamanho_conteudo = len(corpo_resposta)

            # Monta a resposta HTTP
            cabecalho_resposta = (
                f"HTTP/1.1 200 OK\r\n"
                f"Server: MeuServidorPython/1.0\r\n"
                f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
                f"Content-Type: {tipo_conteudo}\r\n"
                f"Content-Length: {tamanho_conteudo}\r\n"
                f"Connection: close\r\n"
                f"\r\n" # Linha em branco crucial que separa cabeçalho e corpo
            )
        else:
            # Resposta 404 Not Found - Arquivo Não Encontrado
            print(f"⚠️  Arquivo não encontrado: {caminho_arquivo}")
            
            corpo_resposta = (
                b"<html><head><title>404 Nao Encontrado</title></head>"
                b"<body><h1>404 Nao Encontrado</h1>"
                b"<p>O recurso solicitado nao foi encontrado neste servidor.</p>"
                b"</body></html>"
            )
            tamanho_conteudo = len(corpo_resposta)
            
            cabecalho_resposta = (
                f"HTTP/1.1 404 Not Found\r\n"
                f"Server: MeuServidorPython/1.0\r\n"
                f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
                f"Content-Type: text/html\r\n"
                f"Content-Length: {tamanho_conteudo}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            )

        # Envia os cabeçalhos (codificados em utf-8)
        conexao.sendall(cabecalho_resposta.encode('utf-8'))
        
        # Envia o corpo da resposta (que já está em bytes)
        conexao.sendall(corpo_resposta)

    except Exception as e:
        print(f"❌ Erro ao lidar com cliente {endereco}: {e}")
    finally:
        conexao.close()
        print(f"🔌 Conexão com {endereco} encerrada.")

def iniciar_servidor():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permite reutilizar o endereço para evitar erro "Address already in use"
    servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        servidor_socket.bind((SERVER_HOST, SERVER_PORT))
        servidor_socket.listen()
        print(f"🚀 Servidor HTTP ouvindo em http://{SERVER_HOST if SERVER_HOST != '0.0.0.0' else '127.0.0.1'}:{SERVER_PORT}")
        print("Pressione Ctrl+C para encerrar.")

        while True:
            conexao_cliente, endereco_cliente = servidor_socket.accept()
            thread_cliente = threading.Thread(target=lidar_com_cliente, args=(conexao_cliente, endereco_cliente))
            thread_cliente.daemon = True
            thread_cliente.start()
            
    except KeyboardInterrupt:
        print("\n M... Encerrando o servidor.")
    except Exception as e:
        print(f"❌ Erro ao iniciar o servidor: {e}")
    finally:
        servidor_socket.close()

if __name__ == "__main__":
    iniciar_servidor()