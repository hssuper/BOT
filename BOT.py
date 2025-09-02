import discord
from discord.ui import Button, View
from discord.ext import commands
import asyncio
import datetime
import io
import traceback
import os
from flask import Flask
from threading import Thread

# --- Configurações do Bot ---
# Por segurança, o token do bot deve ser armazenado em variáveis de ambiente.
# Se for um teste, você pode deixar o token aqui, mas evite em produção.
# Certifique-se de que este token está correto e é o mais recente.
TOKEN = os.environ.get('DISCORD_BOT_TOKEN', 'SEU_TOKEN_AQUI')

# ID do canal onde os relatórios das entrevistas serão enviados.
# Certifique-se de que este ID está correto e que o bot tem permissão de "Anexar Arquivos".
# O ID deve ser um número inteiro, sem aspas!
CHANNEL_RELATORIOS_ID = 1412219134141530243

# IMPORTANTE: ID da MENSAGEM DO BOTÃO aqui.
# Você obtém este ID com o comando /rodar.
# Deve ser um número inteiro, sem aspas!
MENSAGEM_BOTAO_ID = None # Substitua 'None' por um ID real após usar o comando /rodar.


# As perguntas que o bot irá fazer
perguntas_coleta = [
    "Qual seu nick no jogo?",
    "Qual sua idade?",
    "Você possui microfone funcionando?",
    "Em qual turno costuma jogar e quantas horas por dia?",
    "Joga frequentemente nos finais de semana?",
    "Há quanto tempo joga FiveM?",
    "Já foi staff em algum servidor? Se sim, qual cargo e por quanto tempo?",
    "Você se considera uma pessoa calma e paciente?",
    "Já recebeu banimento ou punições em algum servidor? Se sim, qual o motivo?",
    "Como você reagiria se um jogador te ofendesse durante um atendimento?",
    "O que faria se visse um amigo staff abusando do poder?",
    "Pretende continuar fazendo RP normalmente enquanto for staff?",
    "Por que quer fazer parte da equipe?",
    "O que você pode oferecer de diferencial para a staff (ex: habilidades extras)?",
    "Escreva um breve texto sobre você e por que seria um bom membro da staff.",
]

# Configura as permissões (Intents) para o bot.
# O "command_prefix" não é necessário para comandos de barra.
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Cria a instância do bot sem um prefixo de comando de texto
bot = commands.Bot(command_prefix='!', intents=intents)

# Armazena os IDs dos usuários que estão em uma entrevista no momento e seus eventos de cancelamento
active_interviews = {}

# --- Funções Auxiliares ---
async def enviar_relatorio_para_canal(respostas, usuario):
    """Cria um arquivo de texto em memória e o envia para o canal de relatórios."""
    
    # Tenta obter o canal de relatórios, buscando-o diretamente para evitar erros de cache
    try:
        # Garante que o ID do canal é um número inteiro
        canal_relatorios = await bot.fetch_channel(int(CHANNEL_RELATORIOS_ID))
        print(f"Canal de relatórios encontrado via fetch_channel (ID: {CHANNEL_RELATORIOS_ID}).")
    except (ValueError, discord.errors.NotFound):
        print(f"Erro: Canal de relatórios com ID {CHANNEL_RELATORIOS_ID} não encontrado.")
        await usuario.send("❌ Ocorreu um erro ao enviar seu relatório. O canal de relatórios não foi encontrado. Por favor, avise a staff.")
        return
    except discord.errors.Forbidden:
        print(f"Erro: O bot não tem permissão para acessar o canal com ID {CHANNEL_RELATORIOS_ID}.")
        await usuario.send("❌ Ocorreu um erro ao enviar seu relatório. O bot não tem permissão para acessar o canal de relatórios.")
        return
    except Exception as e:
        print(f"Erro inesperado ao tentar encontrar o canal: {e}")
        await usuario.send("❌ Ocorreu um erro ao enviar seu relatório. Por favor, avise a staff.")
        return

    try:
        # Cria o conteúdo do arquivo
        file_content = io.StringIO()
        file_content.write(f"--- Relatório de Entrevista de {usuario.name} ({usuario.id}) ---\n")
        file_content.write(f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for pergunta, dados in respostas.items():
            file_content.write(f"Pergunta: {pergunta}\n")
            file_content.write(f"Resposta: {dados['resposta']}\n")
            file_content.write(f"Tempo levado: {dados['tempo']}\n\n")

        file_content.seek(0)
        discord_file = discord.File(fp=file_content, filename=f"relatorio_{usuario.id}.txt")

        # Envia o arquivo para o canal de relatórios
        await canal_relatorios.send(f"Novo relatório de entrevista de {usuario.mention}:", file=discord_file)
        print("Relatório enviado com sucesso!")
        
    except discord.errors.Forbidden:
        print(f"Erro: O bot não tem permissão para enviar mensagens no canal com ID {CHANNEL_RELATORIOS_ID}.")
        await usuario.send("❌ Ocorreu um erro ao enviar seu relatório. O bot não tem permissão para enviar mensagens no canal de relatórios.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao tentar enviar o relatório: {e}")
        traceback.print_exc()
        await usuario.send("❌ Ocorreu um erro ao tentar enviar seu relatório. Por favor, avise a staff.")

# --- Lógica do Botão e da Entrevista ---
class InterviewView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    @discord.ui.button(label="Começar Entrevista", style=discord.ButtonStyle.green, custom_id="start_interview")
    async def start_button_callback(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in active_interviews:
            await interaction.response.send_message("Você já está em uma entrevista. Por favor, termine a atual antes de começar outra.", ephemeral=True)
            return

        cancel_event = asyncio.Event()
        active_interviews[interaction.user.id] = cancel_event
        
        self.children[0].disabled = True
        self.children[1].disabled = False
        await interaction.response.edit_message(content="Clique em '**Iniciar Entrevista**' e confira suas **Mensagens Diretas**. Você pode clicar em '**Encerrar**' a qualquer momento para cancelar.", view=self)

        try:
            # Pega a mensagem da interação para poder editá-la mais tarde
            self.message = await interaction.original_response()
            await self.run_interview(interaction.user, cancel_event)
        except discord.errors.Forbidden:
            await interaction.followup.send("❌ Não foi possível iniciar a entrevista. Por favor, verifique se suas mensagens diretas (DMs) estão ativadas e tente novamente.", ephemeral=True)
            print(f"Erro: Não foi possível enviar Mensagem Direta para o usuário {interaction.user.name}. Ele(a) pode ter as DMs desativadas.")
        except Exception:
            print(f"Erro inesperado durante a entrevista para o usuário {interaction.user.name}.")
            traceback.print_exc()
            await interaction.user.send("Desculpe, ocorreu um erro durante a entrevista. Por favor, tente novamente.")
        finally:
            if interaction.user.id in active_interviews:
                del active_interviews[interaction.user.id]
                self.children[0].disabled = False
                self.children[1].disabled = True
                await self.message.edit(view=self)
                
    @discord.ui.button(label="Encerrar Entrevista", style=discord.ButtonStyle.red, custom_id="end_interview")
    async def end_button_callback(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id not in active_interviews:
            await interaction.response.send_message("Você não está em uma entrevista para encerrar.", ephemeral=True)
            return
            
        active_interviews[interaction.user.id].set()
        
        await interaction.response.send_message("Entrevista encerrada.", ephemeral=True)

        self.children[0].disabled = False
        self.children[1].disabled = True
        
        try:
            # Garante que o ID da mensagem é um número inteiro
            original_message = await interaction.channel.fetch_message(int(MENSAGEM_BOTAO_ID))
            await original_message.edit(view=self)
        except Exception as e:
            print(f"Erro ao tentar editar a mensagem do botão. Certifique-se de que o ID está correto. Erro: {e}")

    async def run_interview(self, user, cancel_event):
        """Executa a coleta de respostas no DM do usuário."""
        respostas_coletadas = {}
        messages_to_delete = []
        total_perguntas = len(perguntas_coleta)

        print(f"Tentando iniciar a entrevista por DM com o usuário {user.name} ({user.id})")

        dm_channel = await user.create_dm()
        primeira_msg = await dm_channel.send(f"A coleta de respostas vai começar, {user.mention}! O tempo de cada resposta será registrado.")
        messages_to_delete.append(primeira_msg)
        await asyncio.sleep(2)
        
        try:
            for i, pergunta in enumerate(perguntas_coleta):
                embed = discord.Embed(
                    title=f"Pergunta {i+1} de {total_perguntas}",
                    description=f"**{pergunta}**",
                    color=discord.Color.blue()
                )
                
                question_msg = await dm_channel.send(embed=embed)
                messages_to_delete.append(question_msg)

                start_time = datetime.datetime.now()

                try:
                    message_task = asyncio.create_task(self.bot.wait_for('message', check=lambda m: m.author == user and m.channel == dm_channel, timeout=300))
                    cancel_task = asyncio.create_task(cancel_event.wait())

                    done, pending = await asyncio.wait([message_task, cancel_task], return_when=asyncio.FIRST_COMPLETED)
                    for task in pending: task.cancel()

                    if cancel_event.is_set():
                        await dm_channel.send("Sua entrevista foi cancelada.")
                        return

                    msg = message_task.result()
                    messages_to_delete.append(msg)

                    end_time = datetime.datetime.now()
                    tempo_decorrido = (end_time - start_time).total_seconds()
                    
                    respostas_coletadas[pergunta] = {
                        "resposta": msg.content,
                        "tempo": f"{tempo_decorrido:.2f} segundos"
                    }

                except asyncio.TimeoutError:
                    await dm_channel.send("Tempo esgotado! A coleta de respostas foi cancelada.")
                    return
            
            await dm_channel.send("A coleta de respostas terminou! Gerando o arquivo...")
            await enviar_relatorio_para_canal(respostas_coletadas, user)
            await dm_channel.send("O arquivo de resultados foi gerado e enviado para o canal de relatórios com sucesso!")

        finally:
            if messages_to_delete:
                try:
                    await dm_channel.delete_messages(messages_to_delete)
                    print("Mensagens da entrevista apagadas com sucesso.")
                except discord.errors.Forbidden:
                    print("Erro de permissão ao tentar apagar mensagens.")
                except Exception as e:
                    print(f"Erro ao apagar mensagens: {e}")
                    traceback.print_exc()

# --- Eventos do Bot ---
@bot.event
async def on_ready():
    print(f'Bot logado como {bot.user}')
    # Sincroniza os comandos de barra com o Discord
    await bot.tree.sync()
    print("Comandos de barra sincronizados.")
    
    # Se o ID da mensagem do botão estiver configurado, adicione a View persistente
    if MENSAGEM_BOTAO_ID:
        try:
            bot.add_view(InterviewView(bot))
            print("View de entrevista reativada com sucesso.")
        except Exception as e:
            print(f"Não foi possível reativar a view de entrevista: {e}")
            print("Provável causa: o ID da mensagem está incorreto ou a mensagem foi deletada.")
    else:
        print("Atenção: MENSAGEM_BOTAO_ID não está configurado. A View persistente não será ativada.")

# --- Comandos de Barra do Bot ---
@bot.tree.command(name='rodar', description='Cria a mensagem estática com o botão de entrevista.')
@commands.has_permissions(manage_messages=True)
async def rodar_interview_button(interaction: discord.Interaction):
    """Cria a mensagem estática com o botão de entrevista."""
    view = InterviewView(bot)
    message = await interaction.channel.send("Clique no botão abaixo para começar a entrevista para a staff!", view=view)
    
    await interaction.response.send_message(f"✅ Mensagem do botão criada! Use o ID **{message.id}** na variável `MENSAGEM_BOTAO_ID` no seu código para que o botão seja estático.", ephemeral=True)
    print(f"ID da mensagem do botão: {message.id}")
    
@bot.tree.command(name='sair', description='Encerra sua entrevista em andamento.')
async def sair_entrevista(interaction: discord.Interaction):
    """Comando para o usuário sair da entrevista a qualquer momento."""
    if interaction.user.id in active_interviews:
        active_interviews[interaction.user.id].set()
        await interaction.response.send_message("Entrevista encerrada.", ephemeral=True)
    else:
        await interaction.response.send_message("Você não está em uma entrevista para encerrar.", ephemeral=True)

# --- Servidor Web para Manter o Bot Online no Replit ---
# Adiciona um servidor Flask para que o Replit não "suspenda" o bot.
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está online e funcionando!"

def run_flask_server():
    app.run(host='0.0.0.0', port=10000)

# Inicia o servidor Flask em uma nova thread
t = Thread(target=run_flask_server)
t.start()

# Inicia o bot
bot.run(TOKEN)
