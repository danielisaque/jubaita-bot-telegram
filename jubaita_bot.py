# bot.py

import logging
import json
import schedule
import time
import threading
import os  # ### ALTERAÇÃO: Importado para acessar variáveis de ambiente
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv  # ### ALTERAÇÃO: Importado para carregar o arquivo .env

# ### ALTERAÇÃO: Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# ### ALTERAÇÃO: O token é carregado de forma segura do ambiente
# Nunca escreva o token diretamente no código!
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ### ALTERAÇÃO: Adicionada uma verificação para garantir que o token foi carregado
if not TELEGRAM_TOKEN:
    raise ValueError("Variável de ambiente TELEGRAM_TOKEN não encontrada! Crie um arquivo .env ou configure a variável no seu sistema.")


# Configura o log para vermos possíveis erros no terminal
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ARQUIVO_ESCALA = "escala.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_CONFIG = "config.json"

def salvar_dados(dados, nome_arquivo):
    """Função auxiliar para salvar dados em um arquivo JSON."""
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def carregar_dados(nome_arquivo):
    """Função auxiliar para carregar dados de um arquivo JSON."""
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {} # Retorna um dicionário vazio se o arquivo não existir

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Salva o usuário que iniciou o bot para podermos contatá-lo depois."""
    user = update.effective_user
    usuarios = carregar_dados(ARQUIVO_USUARIOS)
    
    # Salva o ID do usuário usando o username como chave (em minúsculas)
    if user.username:
        usuarios[user.username.lower()] = user.id
        salvar_dados(usuarios, ARQUIVO_USUARIOS)
        mensagem = (
            f"Olá, {user.first_name}! 👋\n\n"
            "Seu usuário foi registrado com sucesso. Agora você poderá receber os lembretes da escala de mídia. "
            "Fique tranquilo, não enviarei nenhuma outra mensagem além dos lembretes."
        )
        await update.message.reply_text(mensagem)
    else:
        await update.message.reply_text("Por favor, configure um @username no seu Telegram para que eu possa te encontrar na escala.")

async def receber_escala(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recebe a escala e a salva para verificação futura."""
    
    config = carregar_dados(ARQUIVO_CONFIG)
    topico_configurado_id = config.get("topico_escala_id")

    if not topico_configurado_id:
        await update.message.reply_text("⚠️ Atenção: O bot ainda não foi configurado para um tópico específico.\n\nPor favor, vá ao tópico de escalas e execute o comando /configurar_topico para que eu saiba onde devo funcionar.")
        return

    if update.message.message_thread_id != topico_configurado_id:
        logger.info(f"Comando /escala ignorado porque foi enviado fora do tópico configurado.")
        return

    linhas_brutas = update.message.text.splitlines()

    primeira_linha = linhas_brutas[0].replace('/escala', '').strip()

    todas_as_linhas = [primeira_linha] + linhas_brutas[1:]

    linhas_escala = [linha for linha in todas_as_linhas if linha]

    if not linhas_escala:
        await update.message.reply_text("Uso: /escala\n@usuario, DD/MM/AAAA, Dia da Semana, Nome do Evento\n@outro_usuario, DD/MM/AAAA, Dia da Semana, Nome do Evento")
        return

    escala_atual = carregar_dados(ARQUIVO_ESCALA)
    novas_entradas = 0
    erros = []

    for linha in linhas_escala:
        try:
            # Tenta separar a linha em 4 partes, usando a vírgula como separador
            usuario_raw, data_str, dia_semana, evento = [item.strip() for item in linha.split(',', 3)]
            
            if not usuario_raw.startswith('@'):
                raise ValueError("O nome de usuário deve começar com @.")
            
            usuario = usuario_raw[1:].lower()
            datetime.strptime(data_str, '%d/%m/%Y')
            
            id_escala = f"{data_str}-{usuario}"
            escala_atual[id_escala] = {
                "usuario": usuario,
                "data": data_str,
                "evento": evento,
                "lembrete_09h_enviado": False,
                "lembrete_16h_enviado": False
            }
            novas_entradas += 1
        except ValueError as e:
            logger.warning(f"Erro ao processar a linha '{linha}': {e}")
            erros.append(linha)

    salvar_dados(escala_atual, ARQUIVO_ESCALA)

    mensagem_resposta = f"{novas_entradas} entrada(s) da escala foram salvas com sucesso!"
    if erros:
        mensagem_resposta += "\n\nAs seguintes linhas não puderam ser processadas (verifique o formato '@usuario, DD/MM/AAAA, dia, evento'):\n"
        mensagem_resposta += "\n".join(erros)

    await update.message.reply_text(mensagem_resposta)



async def enviar_lembretes(context: ContextTypes.DEFAULT_TYPE):
    """Verifica a escala e envia o lembrete apropriado para o horário."""
    # Pega o tipo de lembrete (definido no agendamento)
    tipo_lembrete = context.job.data['tipo'] 
    
    logger.info(f"Executando verificação de lembretes - TIPO: {tipo_lembrete.upper()}")
    
    escala = carregar_dados(ARQUIVO_ESCALA)
    usuarios = carregar_dados(ARQUIVO_USUARIOS)
    hoje_str = datetime.now().strftime('%d/%m/%Y')
    
    ids_para_remover = []

    for id_escala, item in escala.items():
        # A data da escala é hoje?
        if item["data"] == hoje_str:
            usuario_escalado = item["usuario"]
            evento = item["evento"]
            chat_id = usuarios.get(usuario_escalado)
            
            # Lembrete das 9h
            if tipo_lembrete == '09h' and not item["lembrete_09h_enviado"]:
                if chat_id:
                    mensagem = f"Olá @{usuario_escalado}! Passando para te lembrar que hoje você está escalado(a) para a mídia no evento: *{evento}*."
                    try:
                        await context.bot.send_message(chat_id=chat_id, text=mensagem, parse_mode='Markdown')
                        logger.info(f"Lembrete de 09h enviado para {usuario_escalado}.")
                        item["lembrete_09h_enviado"] = True
                    except Exception as e:
                        logger.error(f"Falha ao enviar mensagem de 09h para {usuario_escalado}: {e}")
                else:
                    logger.warning(f"Usuário @{usuario_escalado} não encontrado para lembrete de 09h.")
            
            # Lembrete das 16h
            elif tipo_lembrete == '16h' and not item["lembrete_16h_enviado"]:
                if chat_id:
                    mensagem = f"Lembrando! Hoje a mídia está com você!"
                    try:
                        await context.bot.send_message(chat_id=chat_id, text=mensagem)
                        logger.info(f"Lembrete de 16h enviado para {usuario_escalado}.")
                        item["lembrete_16h_enviado"] = True
                    except Exception as e:
                        logger.error(f"Falha ao enviar mensagem de 16h para {usuario_escalado}: {e}")
                else:
                    logger.warning(f"Usuário @{usuario_escalado} não encontrado para lembrete de 16h.")

        # Limpeza: Se a data da escala já passou, marca para remoção
        data_escala_obj = datetime.strptime(item["data"], '%d/%m/%Y').date()
        if data_escala_obj < datetime.now().date():
            ids_para_remover.append(id_escala)

    # Limpa as escalas antigas
    if ids_para_remover:
        logger.info(f"Removendo {len(ids_para_remover)} escalas antigas.")
        for id_escala in ids_para_remover:
            del escala[id_escala]

    salvar_dados(escala, ARQUIVO_ESCALA)

async def configurar_topico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Define o tópico onde o comando /escala deve funcionar."""
    
    # Verifica se a mensagem foi enviada em um tópico
    if not update.message.is_topic_message or not update.message.message_thread_id:
        await update.message.reply_text("Este comando só pode ser usado dentro de um tópico de um grupo.")
        return

    # Pega o ID do tópico atual
    topico_id = update.message.message_thread_id
    
    # Salva o ID no arquivo de configuração
    config = {"topico_escala_id": topico_id}
    salvar_dados(config, ARQUIVO_CONFIG)
    
    logger.info(f"Tópico de escala configurado com o ID: {topico_id}")
    await update.message.reply_text(
        "✅ Sucesso! Este tópico foi configurado para receber as escalas.\n\n"
        "O comando /escala agora só funcionará aqui."
    )

async def apagar_escala(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Apaga todas as entradas da escala para uma data específica."""
    
    # --- Verificação de Tópico (igual ao comando /escala) ---
    config = carregar_dados(ARQUIVO_CONFIG)
    topico_configurado_id = config.get("topico_escala_id")

    if not topico_configurado_id:
        await update.message.reply_text("⚠️ O bot ainda não foi configurado para um tópico. Use /configurar_topico primeiro.")
        return

    if update.message.message_thread_id != topico_configurado_id:
        logger.info(f"Comando /apagarescala ignorado fora do tópico configurado.")
        return
    # --- Fim da Verificação ---

    try:
        # Pega a data que foi enviada junto com o comando
        data_para_apagar = context.args[0]
        # Valida o formato da data
        datetime.strptime(data_para_apagar, '%d/%m/%Y')
    except (IndexError, ValueError):
        # Se nenhuma data for enviada ou o formato estiver errado, envia as instruções
        await update.message.reply_text("Uso incorreto. Por favor, especifique a data.\nExemplo: `/apagarescala 28/09/2025`")
        return

    escala = carregar_dados(ARQUIVO_ESCALA)
    
    # Encontra todas as chaves no dicionário que correspondem à data informada
    ids_para_apagar = [
        id_escala for id_escala, item in escala.items() 
        if item.get("data") == data_para_apagar
    ]

    if not ids_para_apagar:
        await update.message.reply_text(f"Nenhuma escala encontrada para a data {data_para_apagar}.")
        return

    # Apaga as entradas encontradas
    for id_escala in ids_para_apagar:
        del escala[id_escala]

    # Salva o arquivo atualizado
    salvar_dados(escala, ARQUIVO_ESCALA)
    
    logger.info(f"{len(ids_para_apagar)} entrada(s) para a data {data_para_apagar} foram apagadas.")
    await update.message.reply_text(
        f"✅ Sucesso! {len(ids_para_apagar)} entrada(s) da escala para a data {data_para_apagar} foram apagadas."
    )

async def ver_escala_do_mes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra a escala do mês atual a partir da data de hoje."""

    # --- Verificação de Tópico ---
    config = carregar_dados(ARQUIVO_CONFIG)
    topico_configurado_id = config.get("topico_escala_id")

    if not topico_configurado_id:
        await update.message.reply_text("⚠️ O bot ainda não foi configurado para um tópico. Use /configurar_topico primeiro.")
        return
    # --- Fim da Verificação ---

    escala = carregar_dados(ARQUIVO_ESCALA)
    hoje = datetime.now()

    # Filtra as escalas para pegar apenas as do mês e ano atuais, a partir de hoje
    escalas_validas = []
    for item in escala.values():
        try:
            data_escala = datetime.strptime(item['data'], '%d/%m/%Y')
            if (data_escala.month == hoje.month and
                data_escala.year == hoje.year and
                data_escala.date() >= hoje.date()):
                escalas_validas.append(item)
        except (ValueError, KeyError):
            # Ignora entradas mal formatadas no JSON
            continue

    if not escalas_validas:
        await update.message.reply_text("Não há nenhuma escala programada para o restante deste mês.")
        return

    # Ordena as escalas por data
    escalas_validas.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'))

    # Monta a mensagem formatada em Markdown
    mensagem = f"📅 *Escala para o restante de {hoje.strftime('%B').capitalize()}*\n\n"
    
    # Dicionário para agrupar por data
    agrupado_por_data = {}
    for item in escalas_validas:
        data = item['data']
        if data not in agrupado_por_data:
            agrupado_por_data[data] = []
        agrupado_por_data[data].append(item)

    dias_da_semana = {
        'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }

    for data, items in agrupado_por_data.items():
        data_obj = datetime.strptime(data, '%d/%m/%Y')
        dia_semana_en = data_obj.strftime('%A')
        dia_semana_pt = dias_da_semana.get(dia_semana_en, dia_semana_en)

        mensagem += f"*{data} ({dia_semana_pt})*\n"
        for item in items:
            mensagem += f"  - `@{item['usuario']}`: {item['evento']}\n"
        mensagem += "\n" # Adiciona uma linha em branco para separar os dias

    # Envia a mensagem. Usamos parse_mode='Markdown' para formatar o texto.
    await update.message.reply_text(mensagem, parse_mode='Markdown')


def rodar_agendamento(application):
    """Configura e inicia o loop de agendamento para os dois horários."""
    
    # Agenda o lembrete das 09:00
    schedule.every().day.at("09:00").do(
        lambda: application.job_queue.run_once(enviar_lembretes, 0, data={'tipo': '09h'})
    )
    
    # Agenda o lembrete das 16:00
    schedule.every().day.at("16:00").do(
        lambda: application.job_queue.run_once(enviar_lembretes, 0, data={'tipo': '16h'})
    )
    
    logger.info("Agendador configurado para 09:00 e 16:00.")
    
    # Loop infinito para manter o agendador rodando em segundo plano
    while True:
        schedule.run_pending()
        time.sleep(1)

def main() -> None:
    """Inicia o bot e o agendador."""
    # Cria a aplicação do bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Registra os comandos que o bot vai entender
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("escala", receber_escala))
    application.add_handler(CommandHandler("configurar_topico", configurar_topico))
    application.add_handler(CommandHandler("apagarescala", apagar_escala))
    application.add_handler(CommandHandler("escaladomes", ver_escala_do_mes))

    # Inicia o agendador em uma thread separada
    thread = threading.Thread(target=rodar_agendamento, args=(application,))
    thread.daemon = True
    thread.start()
    
    logger.info("Bot iniciado e aguardando comandos...")
    # Inicia o bot para receber atualizações do Telegram
    application.run_polling()

if __name__ == "__main__":
    main()