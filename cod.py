#!/usr/bin/env python3
"""
Monitorador de Preços Sixt com Alertas Telegram
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# ============================================
# CONFIGURAÇÕES DA SUA BUSCA
# ============================================

# Dados extraídos da sua URL da Sixt
PICKUP_LOCATION_ID = "8b9f251d-c402-4915-aee6-d2aeba062777"
DROPOFF_LOCATION_ID = "8b9f251d-c402-4915-aee6-d2aeba062777"
PICKUP_DATE = "2026-12-17T11:30:00"
DROPOFF_DATE = "2026-12-26T11:30:00"
CURRENCY = "BRL"
COUNTRY_CODE = "US"

# Alerta de preço
ALERT_BELOW_PRICE = 2500  # Alerta se preço cair abaixo disso
CURRENT_PRICE = 2850      # Preço atual para calcular economia

# Telegram (vem das variáveis de ambiente)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ============================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.sixt.com",
    "Referer": "https://www.sixt.com/",
}


def get_sixt_prices() -> Optional[Dict[str, Any]]:
    """Busca os preços atuais na API da Sixt."""
    url = "https://web-api.orange.sixt.com/v1/rentaloffers/offers"
    
    params = {
        "pickupStation": PICKUP_LOCATION_ID,
        "returnStation": DROPOFF_LOCATION_ID,
        "pickupDate": PICKUP_DATE,
        "returnDate": DROPOFF_DATE,
        "currency": CURRENCY,
        "vehicleType": "car",
        "areaCode": COUNTRY_CODE.lower(),
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar preços: {e}")
        return None


def parse_prices(data: Dict[str, Any]) -> list:
    """Extrai os preços da resposta da API."""
    offers = []
    
    if not data:
        return offers
    
    offer_list = data.get("offers", data.get("vehicles", []))
    
    for offer in offer_list:
        try:
            vehicle_name = offer.get("vehicleGroupInfo", {}).get("modelExample", {}).get("name", "")
            if not vehicle_name:
                vehicle_name = offer.get("title", offer.get("name", "Veículo"))
            
            prices = offer.get("prices", {})
            total_price = prices.get("totalPrice", {}).get("amount", 0)
            
            if not total_price:
                total_price = offer.get("price", {}).get("amount", 0)
            
            if not total_price:
                total_price = offer.get("totalAmount", 0)
            
            currency = prices.get("totalPrice", {}).get("currency", CURRENCY)
            
            if total_price > 0:
                offers.append({
                    "vehicle": vehicle_name,
                    "price": float(total_price),
                    "currency": currency,
                })
        except (KeyError, TypeError):
            continue
    
    return offers


def get_lowest_price(offers: list) -> Optional[Dict]:
    """Retorna a oferta com menor preço."""
    if not offers:
        return None
    return min(offers, key=lambda x: x["price"])


def send_telegram_alert(message: str) -> bool:
    """Envia mensagem via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram não configurado")
        print(f"📝 Mensagem: {message}")
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
        print("✅ Alerta enviado via Telegram!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar Telegram: {e}")
        return False


def format_price(price: float, currency: str = "BRL") -> str:
    """Formata o preço para exibição."""
    if currency == "BRL":
        return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{currency} {price:,.2f}"


def check_prices():
    """Função principal que verifica os preços."""
    print(f"\n{'='*50}")
    print(f"🚗 Monitorador de Preços Sixt")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*50}")
    
    print("\n🔍 Buscando preços na Sixt...")
    data = get_sixt_prices()
    
    if not data:
        print("❌ Não foi possível obter os preços")
        return
    
    offers = parse_prices(data)
    
    if not offers:
        print("⚠️  Nenhuma oferta encontrada")
        print(f"📝 Resposta da API: {json.dumps(data, indent=2)[:500]}...")
        return
    
    lowest = get_lowest_price(offers)
    current_price = lowest["price"]
    
    print(f"\n📊 Resultados:")
    print(f"   Menor preço: {format_price(current_price)}")
    print(f"   Veículo: {lowest['vehicle']}")
    print(f"   Alvo: {format_price(ALERT_BELOW_PRICE)}")
    
    savings = CURRENT_PRICE - current_price
    if savings > 0:
        print(f"   💰 Economia vs inicial: {format_price(savings)}")
    
    # Verifica se deve enviar alerta
    if current_price <= ALERT_BELOW_PRICE:
        print(f"\n🚨 PREÇO ABAIXO DO ALVO!")
        
        message = f"""🚗 <b>ALERTA DE PREÇO SIXT!</b>

💰 <b>Preço encontrado:</b> {format_price(current_price)}
🎯 <b>Seu alvo era:</b> {format_price(ALERT_BELOW_PRICE)}
💵 <b>Economia:</b> {format_price(CURRENT_PRICE - current_price)}

🚙 <b>Veículo:</b> {lowest['vehicle']}
📍 <b>Local:</b> Naperville/Marriott
📅 <b>Período:</b> 17-26/Dez/2026

⚡ <b>Reserve agora!</b>"""
        
        send_telegram_alert(message)
    else:
        diff = current_price - ALERT_BELOW_PRICE
        print(f"\n📈 Preço ainda {format_price(diff)} acima do alvo")
        
        # Envia resumo diário (opcional - comente se não quiser)
        # send_telegram_alert(f"📊 Sixt: {format_price(current_price)} (alvo: {format_price(ALERT_BELOW_PRICE)})")


if __name__ == "__main__":
    check_prices()
