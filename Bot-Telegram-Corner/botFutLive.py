import requests
from fake_useragent import UserAgent
import telebot
import time
from datetime import datetime

# Telegram 
today = datetime.now().strftime("%Y-%m-%d")
token =  # token do bot Telegram
chat_id = # chat_id do grupo 
bot = telebot.TeleBot(token)
jogos_enviados = []

# Instância do UserAgent para simular um navegador
ua = UserAgent()

def obter_dados_api():
    url = "https://playscores.sportsat.app/gateway/api/v2/fixtures-svc/livescores?includes=league,stats,pressureStats&take=3000"
    headers = {'Accept': 'application/json', 'Origin': 'https://www.playscores.com', 'User-Agent': ua.random}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return None

def construir_mensagem(game, strategy):
    home_team = game["homeTeam"]["name"]
    away_team = game["awayTeam"]["name"]
    league = game["league"]["name"]
    home_score = game['scores']['homeTeamScore']
    away_score = game['scores']['awayTeamScore']
    minute = game["currentTime"]["minute"]
    convert_nome = home_team.replace(" ", "+")
    link_bet365 = f"https://www.bet365.com/#/AX/K%5E{convert_nome}/"
    
    # Detalhes estatísticos
    stats = {
        'home_exg': game['pressureStats']['exg']['home'],
        'away_exg': game['pressureStats']['exg']['away'],
        'home_appm1': game['pressureStats']['appm1']['home'],
        'away_appm1': game['pressureStats']['appm1']['away'],
        # Adicione mais estatísticas conforme necessário...
    }

    mensagem = f'''🔥 ALERTA GB BOT 🔥

🆚 <b>{home_team} x {away_team}</b>
🏆 {league}
⏰ {minute}' minutos

🚨 <b>{strategy}</b>

⚠️ Respeite sua meta diária!

🔍 <b>Estatísticas(Casa - Fora):</b>
📈 Placar: {home_score} - {away_score}
⛳️ Escanteios: {game['stats']['corners']['home']} - {game['stats']['corners']['away']}

📲 <a href="{link_bet365}">link do jogo</a>'''

    return mensagem

def analisar_jogo(game):
    minute = game.get("currentTime", {}).get("minute")

    if minute is None or not isinstance(minute, int):
        return None

    home_score = game['scores']['homeTeamScore']
    away_score = game['scores']['awayTeamScore']
    score_difference = (home_score - away_score)

    if -1 <= score_difference <= 1:

        # Verifique se 'pressureStats' e 'exg' existem e não são None antes de prosseguir
        pressure_stats = game.get('pressureStats')
        if pressure_stats is None:
            return None  # Se 'pressureStats' for None, não há como prosseguir

        exg_home = pressure_stats.get('exg', {}).get('home', 0)
        exg_away = pressure_stats.get('exg', {}).get('away', 0)

        home_score = game.get('scores', {}).get('homeTeamScore', 0)
        away_score = game.get('scores', {}).get('awayTeamScore', 0)

        # Verificações semelhantes podem ser necessárias para 'mh1' e 'appm2' se eles também puderem ser None
        mh1_stats = pressure_stats.get('mh1', {})
        mh1_home = mh1_stats.get('home', 0)
        mh1_away = mh1_stats.get('away', 0)

        appm1_stats = pressure_stats.get('appm1', {})
        appm1_home = appm1_stats.get('home', 0)
        appm1_away = appm1_stats.get('away', 0)

        shots_Ongoal = game.get('stats', {}).get('shotsOngoal', {})
        shots_Ongoal_home = shots_Ongoal.get('home', 0)
        shots_Ongoal_away = shots_Ongoal.get('away', 0)
        
        shots_Offgoal = game.get('stats', {}).get('shots_Offgoal', {})
        shots_Offgoal_home = shots_Offgoal.get('home', 0)
        shots_Offgoal_away = shots_Offgoal.get('away', 0)

        total_corners = game.get('stats', {}).get('corners', {})
        total_corners_home = total_corners.get('home', 0)
        total_corners_away = total_corners.get('away', 0)

        # Estratégia para Over Gols HT - Casa
        if home_score <= away_score and appm1_home > 0.7 and exg_home >= 1.5 and 15 <= minute <= 30:
            return "Over Gol HT Casa"

        # Estratégia para Over Gols FT - Casa
        if home_score <= away_score and appm1_home >= 0.7 and exg_home >= 1.5 and 50 <= minute <= 75:
            return "Over Gol FT Casa"
        
        # Estratégia para Over Gols HT - Fora
        if home_score >= away_score and appm1_away >= 0.7 and exg_away >= 1.5 and 15 <= minute <= 30:
            return "Over Gol HT Fora"

        # Estratégia para Over Gols FT - Fora
        if home_score >= away_score and appm1_away >= 0.7 and exg_away >= 1.5 and 50 <= minute <= 75:
            return "Over Gol FT Fora"

        # Estratégia para Over Cantos HT - Casa
        if home_score <= away_score and appm1_home >= 1.5 and 30 <= minute <= 35:
            return "Over Cantos HT Casa"

        # Estratégia para Over Cantos HT - Fora
        if home_score >= away_score and appm1_away >= 1.5 and 30 <= minute <= 38:   
            return "Over Cantos HT Fora"

        # Estratégia para Over Cantos FT - Casa
        if home_score <= away_score and appm1_home >= 1.5 and 75 <= minute <= 88:
            return "Over Cantos FT Casa"

        # Estratégia para Over Cantos FT - Fora
        if home_score >= away_score and appm1_away >= 1.5 and 75 <= minute <= 88:
            return "Over Cantos FT Fora"

    return None

def verificar_dados_e_enviar(dados):
    if dados is None:
        return

    for game in dados['data']:
        if game is None:
            continue
        fixture_id = game['fixtureId']
        if fixture_id in jogos_enviados:
            continue

        strategy = analisar_jogo(game)
        if strategy:
            mensagem = construir_mensagem(game, strategy)
            enviar_mensagem_telegram(mensagem, chat_id)
            jogos_enviados.append(fixture_id)

def enviar_mensagem_telegram(mensagem, chat_id):
    try:
        bot.send_message(chat_id, mensagem, disable_web_page_preview=True, parse_mode='HTML')
    except Exception as e:
        return

while True:
    dados = obter_dados_api()
    verificar_dados_e_enviar(dados)
    time.sleep(180)  # Intervalo entre verificações
