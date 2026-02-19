#!/usr/bin/env python3
"""
Monitorador de Preços Sixt com Alertas Telegram
"""

import os
import requests
from datetime import datetime

# ============================================
# CONFIGURAÇÕES
# ============================================

# Alerta de preço
ALERT_BELOW_PRICE = 2500  # Alerta se preço cair abaixo disso
CURRENT_PRICE = 2850      # Preço inicial para calcular economia

# Telegram (vem das variáveis de ambiente)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# URL da sua busca na Sixt (para referência)
SIXT_URL = "https://www.sixt.com/betafunnel/#/offerlist?wakz=BRL&zen_pu_location=8b9f251d-c402-4915-aee6-d2aeba062777&zen_do_location=8b9f251d-c402-4915-aee6-d2aeba062777&zen_pu_time=2026-12-17T11%3A30&zen_do_time=2026-12-26T11%3A30"

# ============================================

def send_telegram_message(message: str) -> bool:
    """Envia mensagem via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram não configurado")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Mensagem enviada via Telegram!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar Telegram: {e}")
        return False


def format_price(price: float) -> str:
    """Formata o preço para exibição."""
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def check_prices():
    """Função principal que verifica os preços."""
    print(f"\n{'='*50}")
    print(f"🚗 Monitorador de Preços Sixt")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*50}")
    
    # Como a API da Sixt não está acessível diretamente,
    # vamos usar uma abordagem alternativa com notificação de status
    
    print(f"\n📊 Configuração atual:")
    print(f"   Preço inicial: {format_price(CURRENT_PRICE)}")
    print(f"   Alvo: {format_price(ALERT_BELOW_PRICE)}")
    print(f"   Local: Naperville/Marriott")
    print(f"   Período: 17-26/Dez/2026")
    
    # Envia mensagem de status no Telegram
    message = f"""🚗 <b>Monitor Sixt - Status</b>

📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

📊 <b>Configuração:</b>
- Preço inicial: {format_price(CURRENT_PRICE)}
- Alvo: {format_price(ALERT_BELOW_PRICE)}
- Local: Naperville/Marriott
- Período: 17-26/Dez/2026

⚠️ <b>Nota:</b> A API da Sixt não permite consulta automática de preços. 

💡 <b>Recomendação:</b> Use o AutoSlash para monitoramento automático:
https://www.autoslash.com/track

Ou verifique manualmente:
https://www.sixt.com"""

    send_telegram_message(message)
    print("\n✅ Mensagem de status enviada!")


if __name__ == "__main__":
    check_prices()
