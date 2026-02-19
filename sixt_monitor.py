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

# Dados da sua busca (extraídos da URL)
PICKUP_LOCATION_ID = "dce4741f-3763-4aa1-a6cd-917db41db2f5"
DROPOFF_LOCATION_ID = "dce4741f-3763-4aa1-a6cd-917db41db2f5"
BRANCH_ID = "47567"
PICKUP_DATE = "2026-12-17T12:00"
DROPOFF_DATE = "2026-12-26T12:00"
OFFER_MATRIX_ID = "56b5908b-27a4-427c-9e4d-094e411f3389"

# Alerta de preço
ALERT_BELOW_PRICE = 2500
CURRENT_PRICE = 2850

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ============================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
    "Origin": "https://www.sixt.com",
    "Referer": "https://www.sixt.com/",
}


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
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")
        return False


def format_price(price: float) -> str:
    return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def try_api_v1():
    """Tenta API v1 da Sixt."""
    url = "https://web-api.orange.sixt.com/v1/rentaloffers/offers"
    params = {
        "pickupStation": BRANCH_ID,
        "returnStation": BRANCH_ID,
        "pickupDate": PICKUP_DATE,
        "returnDate": DROPOFF_DATE,
        "currency": "BRL",
        "vehicleType": "car",
        "areaCode": "us",
    }
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def try_api_v2():
    """Tenta API v2 da Sixt."""
    url = f"https://web-api.orange.sixt.com/v2/rentaloffers/offers"
    params = {
        "pickupStation": BRANCH_ID,
        "returnStation": BRANCH_ID,
        "pickupDate": PICKUP_DATE,
        "returnDate": DROPOFF_DATE,
        "currency": "BRL",
        "vehicleType": "car",
    }
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def try_api_locations():
    """Tenta API com location IDs."""
    url = "https://web-api.orange.sixt.com/v1/locations"
    params = {"term": "Naperville"}
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def try_rental_api():
    """Tenta API de rental."""
    url = "https://www.sixt.com/php/reservation/offermatrix"
    params = {
        "pickupStation": BRANCH_ID,
        "returnStation": BRANCH_ID,
        "pickupDate": PICKUP_DATE,
        "returnDate": DROPOFF_DATE,
    }
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def get_prices():
    """Tenta várias APIs para obter preços."""
    apis = [
        ("API v1", try_api_v1),
        ("API v2", try_api_v2),
        ("API Locations", try_api_locations),
        ("API Rental", try_rental_api),
    ]
    
    results = {}
    for name, func in apis:
        try:
            print(f"   Tentando {name}...")
            data = func()
            results[name] = {"success": True, "data": data}
            print(f"   ✅ {name} funcionou!")
        except Exception as e:
            results[name] = {"success": False, "error": str(e)}
            print(f"   ❌ {name}: {e}")
    
    return results


def extract_prices(results):
    """Extrai preços dos resultados das APIs."""
    offers = []
    
    for name, result in results.items():
        if not result.get("success"):
            continue
        
        data = result.get("data", {})
        
        # Tenta diferentes estruturas de resposta
        offer_list = data.get("offers", [])
        if not offer_list:
            offer_list = data.get("vehicles", [])
        if not offer_list:
            offer_list = data.get("results", [])
        
        for offer in offer_list:
            try:
                # Tenta extrair nome do veículo
                vehicle = offer.get("vehicleGroupInfo", {}).get("modelExample", {}).get("name", "")
                if not vehicle:
                    vehicle = offer.get("title", offer.get("name", "Veículo"))
                
                # Tenta extrair preço
                price = 0
                if "prices" in offer:
                    price = offer["prices"].get("totalPrice", {}).get("amount", 0)
                if not price and "price" in offer:
                    price = offer["price"].get("amount", offer["price"]) if isinstance(offer["price"], dict) else offer["price"]
                if not price:
                    price = offer.get("totalAmount", offer.get("total", 0))
                
                if price and float(price) > 0:
                    offers.append({
                        "vehicle": vehicle,
                        "price": float(price),
                        "source": name,
                    })
            except:
                continue
    
    return offers


def check_prices():
    """Função principal."""
    print(f"\n{'='*50}")
    print(f"🚗 Monitorador de Preços Sixt")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*50}")
    
    print(f"\n📋 Configuração:")
    print(f"   Local: Naperville/Marriott")
    print(f"   Período: 17-26/Dez/2026")
    print(f"   Preço inicial: {format_price(CURRENT_PRICE)}")
    print(f"   Alvo: {format_price(ALERT_BELOW_PRICE)}")
    
    print(f"\n🔍 Buscando preços...")
    results = get_prices()
    
    # Conta sucessos e falhas
    successes = sum(1 for r in results.values() if r.get("success"))
    failures = len(results) - successes
    
    print(f"\n📊 Resultado: {successes} APIs funcionaram, {failures} falharam")
    
    # Extrai preços
    offers = extract_prices(results)
    
    if offers:
        lowest = min(offers, key=lambda x: x["price"])
        print(f"\n💰 Menor preço encontrado: {format_price(lowest['price'])}")
        print(f"   Veículo: {lowest['vehicle']}")
        
        if lowest["price"] <= ALERT_BELOW_PRICE:
            message = f"""🚨 <b>ALERTA DE PREÇO SIXT!</b>

💰 <b>Preço:</b> {format_price(lowest['price'])}
🎯 <b>Alvo:</b> {format_price(ALERT_BELOW_PRICE)}
💵 <b>Economia:</b> {format_price(CURRENT_PRICE - lowest['price'])}

🚙 {lowest['vehicle']}
📍 Naperville/Marriott
📅 17-26/Dez/2026

⚡ Reserve agora!"""
            send_telegram_message(message)
        else:
            diff = lowest["price"] - ALERT_BELOW_PRICE
            print(f"   📈 Ainda {format_price(diff)} acima do alvo")
            
            # Envia status
            message = f"""📊 <b>Monitor Sixt - Status</b>

📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

💰 Menor preço: {format_price(lowest['price'])}
🎯 Alvo: {format_price(ALERT_BELOW_PRICE)}
📈 Diferença: {format_price(diff)} acima

🚙 {lowest['vehicle']}
📍 Naperville/Marriott"""
            send_telegram_message(message)
    else:
        print("\n⚠️  Nenhum preço encontrado nas APIs")
        
        # Salva respostas para debug
        debug_info = {name: str(r)[:500] for name, r in results.items()}
        print(f"\n📝 Debug: {json.dumps(debug_info, indent=2)}")
        
        # Envia status mesmo sem preço
        message = f"""📊 <b>Monitor Sixt - Status</b>

📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

⚠️ Não foi possível obter preços automaticamente.

📍 Naperville/Marriott
📅 17-26/Dez/2026
🎯 Alvo: {format_price(ALERT_BELOW_PRICE)}

💡 Verifique manualmente:
https://www.sixt.com"""
        send_telegram_message(message)


if __name__ == "__main__":
    check_prices()
