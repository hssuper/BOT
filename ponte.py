# Esse código é a "ponte" entre o webhook de pagamento e o seu servidor Lua.
# Você precisa instalar o Flask: pip install Flask

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# URL e token do seu servidor de jogo para enviar comandos
# Você precisará configurar isso no seu servidor Lua.
# Por exemplo, uma API que aceita comandos via HTTP.
SERVIDOR_JOGO_URL = "http://localhost:30120/exec_command" 
TOKEN_DE_SEGURANCA = "seu-token-secreto"

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    # Recebe os dados do webhook da plataforma de pagamento
    dados_webhook = request.json

    try:
        # Extrai o ID do usuário e a chave do produto dos dados
        # O formato dos dados_webhook depende da sua plataforma de pagamento.
        user_id = dados_webhook["user_id"]
        chave_do_produto = dados_webhook["chave_do_produto"]

        # Envia um comando para o servidor Lua para creditar o item
        resposta_servidor = requests.post(
            SERVIDOR_JOGO_URL,
            json={
                "command": "darItemAoUsuario",
                "args": [user_id, chave_do_produto],
                "token": TOKEN_DE_SEGURANCA
            }
        )
        
        # Verifica se o comando foi executado com sucesso no servidor Lua
        if resposta_servidor.status_code == 200:
            return jsonify({"status": "sucesso", "mensagem": "Item creditado no jogo."})
        else:
            return jsonify({"status": "erro", "mensagem": "Falha ao creditar item no jogo."}), 500

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 400

if __name__ == "__main__":
    # Roda o servidor web na porta 5000
    app.run(port=5000, debug=True)