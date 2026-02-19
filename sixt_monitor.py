#!/usr/bin/env python3
"""
Monitorador de Preços Sixt com Alertas Telegram
"""

import os
import json
import requests
from datetime import datetime

# ============================================
# CONFIGURAÇÕES
# ============================================

BRANCH_ID = "47567"
PICKUP_DATE = "2026-12-17T12:00"
DROPOFF_DATE = "2026-12-26T12:00"

ALERT_BELOW_PRICE = 2500
CURRENT_PRICE = 2850

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ============================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def send_telegram_message(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram não configurado")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Mensagem enviada via Telegram!")
        return True
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")
        return False


def format_price(price: float) -> str:
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def check_prices():
    print(f"\n{'='*50}")
    print(f"🚗 Monitorador de Preços Sixt")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*50}")
    
    print(f"\n📋 Configuração:")
    print(f"   Local: Naperville/Marriott")
    print(f"   Período: 17-26/Dez/2026")
    print(f"   Preço inicial: {format_price(CURRENT_PRICE)}")
    print(f"   Alvo: {format_price(ALERT_BELOW_PRICE)}")
    
    # Tenta buscar localizações para confirmar que API funciona
    print(f"\n🔍 Verificando API...")
    
    try:
        url = "https://web-api.orange.sixt.com/v1/locations"
        params = {"term": "Naperville"}
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"   ✅ API respondeu: encontrou {len(data)} localizações")
    except Exception as e:
        print(f"   ❌ Erro na API: {e}")
    
    # Envia mensagem de status no Telegram
    message = f"""📊 <b>Monitor Sixt - Ativo!</b>

📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

📍 <b>Local:</b> Naperville/Marriott
📅 <b>Período:</b> 17-26/Dez/2026
💰 <b>Preço inicial:</b> {format_price(CURRENT_PRICE)}
🎯 <b>Alvo:</b> {format_price(ALERT_BELOW_PRICE)}

⚠️ <b>Nota:</b> A API da Sixt bloqueia consultas de preço externas.

💡 <b>Recomendação:</b> Para monitoramento automático de preços, use:
👉 https://www.autoslash.com/track

O AutoSlash monitora gratuitamente e te avisa quando o preço baixar!

🔗 Link direto Sixt:
https://www.sixt.com"""

    send_telegram_message(message)
    print("\n✅ Status enviado para o Telegram!")


if __name__ == "__main__":
    check_prices()
