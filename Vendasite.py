# Backend em Python (adaptado para um carrinho)
from flask import Flask, request, jsonify
from flask_cors import CORS
import qrcode
import base64
import io
import requests

app = Flask(__name__)
CORS(app)

# Seu catálogo de produtos (pode ser o mesmo do seu código Lua)
loja = {
    "vip_member": { "nome": "VIP Bronze", "valor": 49.90 },
    "Retirar_banimento": { "nome": "Retirar Banimento", "valor": 25.00 },
    "caixa_misteriosa": { "nome": "Caixa Misteriosa", "valor": 15.00, "id_item": 120 },
    "arma_lendaria": { "nome": "Arma Lendária", "valor": 100.00, "id_item": 350 },
}

# URL para enviar a notificação ao seu servidor Lua
SERVIDOR_JOGO_URL = "http://seu_endereco_servidor_lua:30120/daritem" 
TOKEN_DE_SEGURANCA = "seu-token-secreto"

# Rota para iniciar o checkout
@app.route('/checkout', methods=['POST'])
def checkout():
    # Recebe os itens do carrinho do seu site (HTML/JS)
    carrinho = request.json.get('carrinho', [])
    user_id = request.json.get('user_id') # Assumindo que você tem o ID do usuário
    
    # 1. Validação do carrinho
    total = 0
    itens_comprados = []
    for item_chave in carrinho:
        if item_chave not in loja:
            return jsonify({'error': f"Item '{item_chave}' não encontrado"}), 400
        total += loja[item_chave]['valor']
        itens_comprados.append(item_chave)

    # 2. Criação do pagamento
    # Lógica para se comunicar com a API de pagamento.
    # Exemplo: https://api.mercadopago.com/pagamentos
    link_de_pagamento = f"https://sua-plataforma-pagamento.com/pagar?carrinho={','.join(itens_comprados)}&user_id={user_id}"

    # 3. Gerar QR Code e enviar de volta para o site
    img_buffer = io.BytesIO()
    img = qrcode.make(link_de_pagamento)
    img.save(img_buffer, "PNG")
    img_buffer.seek(0)
    qrcode_base64 = base64.b64encode(img_buffer.getvalue()).decode('ascii')
    
    return jsonify({
        'qrcode': f"data:image/png;base64,{qrcode_base64}",
        'link_pagamento': link_de_pagamento,
        'total': total
    })

# Rota do webhook para confirmar o pagamento
@app.route("/confirmacao_pagamento", methods=["POST"])
def confirmacao_pagamento():
    dados = request.json
    
    # Lógica para verificar a autenticidade do webhook e os dados
    if dados['status'] == 'aprovado':
        user_id = dados['user_id']
        itens_comprados = dados['itens'] # Lista de itens comprados
        
        # Envia a notificação para o servidor Lua
        requests.post(
            SERVIDOR_JOGO_URL,
            json={
                "user_id": user_id,
                "itens": itens_comprados,
                "token": TOKEN_DE_SEGURANCA
            }
        )
        return jsonify({"mensagem": "Sucesso!"})
    return jsonify({"mensagem": "Pagamento pendente ou falho."})

if __name__ == "__main__":
    app.run(debug=True, port=5000)