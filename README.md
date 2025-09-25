# 🤖 Bot de Escala para Telegram 📅

Um bot simples, porém poderoso, para gerenciar escalas e enviar lembretes automáticos para membros de um grupo no Telegram. Perfeito para organizar escalas de trabalho, plantões, ou qualquer atividade recorrente que precise de lembretes.

## ✨ Funcionalidades Principais

  - **📝 Cadastro de Escalas**: Envie a escala da semana ou do mês de uma só vez.
  - **🔔 Lembretes Automáticos**: O bot envia lembretes automáticos em horários pré-configurados (09:00 e 16:00) para a pessoa que está na escala do dia.
  - **🗓️ Visualização da Escala**: Consulte facilmente a escala programada para o restante do mês.
  - **🗑️ Gerenciamento Simples**: Apague todas as entradas de uma data específica com um único comando.
  - **🎯 Operação em Tópicos**: Configure o bot para funcionar apenas em um tópico específico do seu grupo, mantendo o chat principal limpo.
  - **🔒 Seguro**: O código é preparado para não expor o token do bot, utilizando variáveis de ambiente.

## 🛠️ Tecnologias Utilizadas

  - [Python](https://www.python.org/)
  - [python-telegram-bot](https://python-telegram-bot.org/) - A biblioteca para interagir com a API do Telegram.
  - [schedule](https://schedule.readthedocs.io/en/stable/) - Para agendamento das tarefas de lembrete.
  - [python-dotenv](https://github.com/theskumar/python-dotenv) - Para gerenciar as variáveis de ambiente de forma segura.

## 📌 Como Usar (Comandos)

Interaja com o bot usando os seguintes comandos dentro do seu grupo no Telegram.

-----

### 1\. `/start` (no privado com o bot)

Todo usuário que for participar da escala deve primeiro iniciar uma conversa privada com o bot e enviar o comando `/start`. Isso registra o usuário e permite que o bot envie os lembretes.

### 2\. `/configurar_topico` (dentro de um tópico do grupo)

Este deve ser o **primeiro comando a ser executado no grupo**. Vá até o tópico onde as escalas serão gerenciadas e envie o comando. O bot passará a aceitar os outros comandos apenas naquele tópico.

### 3\. `/escala` (no tópico configurado)

Para adicionar novas datas à escala. Você pode enviar várias linhas de uma vez.
**Formato:** `@usuario, DD/MM/AAAA, Dia da Semana, Nome do Evento`

**Exemplo:**

```
/escala @joao, 25/09/2025, Quinta-feira, Reunião de Alinhamento
@maria, 26/09/2025, Sexta-feira, Gravação Podcast
@ana, 29/09/2025, Segunda-feira, Live Semanal
```

### 4\. `/escaladomes` (em qualquer lugar do grupo)

Mostra uma lista formatada de todas as escalas agendadas do dia atual até o fim do mês.

### 5\. `/apagarescala` (no tópico configurado)

Remove todas as entradas de uma data específica. Útil para corrigir escalas enviadas por engano.
**Formato:** `/apagarescala DD/MM/AAAA`

**Exemplo:**

```
/apagarescala 29/09/2025
```

-----

## 📂 Estrutura do Projeto

```
.
├── bot.py              # Lógica principal e comandos do bot
├── requirements.txt      # Dependências do projeto
├── .gitignore          # Arquivos e pastas ignorados pelo Git
└── README.md           # Este arquivo que você está lendo :)
```

Os arquivos `escala.json`, `usuarios.json`, `config.json` e `.env` serão criados durante a execução ou configuração e são intencionalmente ignorados pelo `.gitignore` para proteger dados sensíveis.
