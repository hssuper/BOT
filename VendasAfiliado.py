import discord
from discord.ext import commands
import qrcode
from PIL import Image

# Configuração do bot com as permissões (intents)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Banco de dados de produtos, onde a CHAVE é o identificador
# do PRODUTO + do AFILIADO. Aqui você pode modificar as porcentagens.
produtos_afiliados = {
    'Vips ouro': {
        'nome': 'Vips ouro',
        'valor': 197.50,
        'afiliado': 'vip',
    },
    'Vips prata': {
        'nome': 'VIps prata',
        'valor': 50.00,
        'afiliado': 'Maria',
    },
    # Adicione mais produtos/afiliados aqui
}

# Simulação da função que gera o QR Code
def gerar_qrcode(link_de_pagamento, nome_arquivo):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(link_de_pagamento)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(nome_arquivo)

# Evento para quando o bot receber uma mensagem
@bot.event
async def on_message(message):
    # Ignora mensagens do próprio bot
    if message.author == bot.user:
        return

    # A mensagem que o usuário envia é a chave do afiliado.
    chave_afiliado = message.content.strip()

    # Valida se a chave de afiliado existe no seu dicionário de produtos
    if chave_afiliado in produtos_afiliados:
        produto = produtos_afiliados[chave_afiliado]
        
        # Envia a mensagem de confirmação
        await message.channel.send(f'Chave de afiliado validada! Você está comprando o produto **{produto["nome"]}**.')
        await message.channel.send(f'O valor é R${produto["valor"]:.2f}. O afiliado {produto["afiliado"]} receberá {produto["comissao_porcentagem"]}% de comissão.')
        await message.channel.send('Gerando o QR Code para pagamento...')

        # Lógica para gerar o link de pagamento com a chave e outras informações
        link_de_pagamento = f"https://sua-plataforma.com/pagamento?id_produto={chave_afiliado}&valor={produto['valor']}"

        # Gerar e enviar o QR Code
        nome_arquivo_qrcode = f"{chave_afiliado}.png"
        gerar_qrcode(link_de_pagamento, nome_arquivo_qrcode)
        
        await message.channel.send(file=discord.File(nome_arquivo_qrcode))
        await message.channel.send('Seu pagamento foi gerado. Escaneie o QR Code acima para efetuar o pagamento.')

    else:
        # Se a mensagem não for uma chave válida
        # Evita responder a qualquer mensagem para não poluir o canal
        pass
        
# Código para o bot exibir a mensagem estática
async def display_prompt():
    canal = bot.get_channel(SEU_ID_DO_CANAL_AQUI)  # Substitua pelo ID do canal do Discord
    if canal:
        await canal.send('**Efetue sua compra agora!**')

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    await display_prompt() # Exibe a mensagem de prompt quando o bot é iniciado

# Coloque o token do seu bot aqui
# bot.run('SEU_TOKEN_AQUI')