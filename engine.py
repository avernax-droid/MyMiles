import requests
from scraper import obter_token_sessao
import time

def processar_resultados(itinerarios):
    voos_formatados = []
    
    for item in itinerarios:
        try:
            out = item.get('outboundFlight') or {}
            inb = item.get('inboundFlight') or {}

            # --- CÁLCULO DE MILHAS (PONTOS) ---
            raw_price = int(item.get('bestPrice', 0))
            valor_milhas = int(raw_price / 10) 
            preco_display = f"{valor_milhas:,} pts".replace(",", ".")

            # --- TAXAS DE EMBARQUE ---
            # Se a API não enviar taxas, o Sniper exibirá "Ver no Link" 
            # para o usuário conferir direto no checkout da Cia.
            raw_tax = (
                item.get('totalTaxes') or 
                item.get('priceDetail', {}).get('totalTaxes') or 
                item.get('priceDetail', {}).get('taxes') or 0
            )

            if raw_tax > 0:
                taxa_reais = float(raw_tax) / 100
                taxa_display = f"R$ {taxa_reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                taxa_display = "Ver no Link"

            def limpar_trecho(flight, sentido, preco_info, taxa_info):
                dt = flight.get('departureDateTime', {})
                horario = f"{dt.get('hour', 0):02d}:{dt.get('minute', 0):02d}" if 'hour' in dt else "--:--"
                paradas = flight.get('stopsCount', 0)
                txt_escalas = "DIRETO" if paradas == 0 else f"{paradas} escala(s)"

                return {
                    "sentido": sentido,
                    "voo": flight.get('carrierName', '---'),
                    "trecho": f"{flight.get('departureAirport', '---')} ➔ {flight.get('arrivalAirport', '---')}",
                    "horario": horario,
                    "duracao": flight.get('durationText', ''),
                    "escalas": txt_escalas,
                    "preco": preco_info, 
                    "taxas": taxa_info,
                    "link": item.get('bookingLink', '#')
                }

            if out:
                voos_formatados.append(limpar_trecho(out, "IDA", preco_display, taxa_display))
            if inb and inb.get('departureAirport'):
                voos_formatados.append(limpar_trecho(inb, "VOLTA", "------", "------"))

        except Exception as e:
            print(f"⚠️ Erro ao processar item: {e}")
            continue

    return voos_formatados

def buscar_voos_completos(origem, destino, data_ida, data_volta=None):
    token = obter_token_sessao(origem, destino, data_ida, data_volta)
    if not token:
        return []

    url_api = f"https://sky-api-778236310566.us-central1.run.app/search/poll/{token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://bestflightsprices.com",
        "Referer": "https://bestflightsprices.com/"
    }

    # Polling de 20 tentativas para garantir carregamento internacional
    for i in range(20):
        print(f"📡 [ENGINE] Polling Sky-API ({i+1}/20)...")
        try:
            response = requests.get(url_api, headers=headers, timeout=30)
            if response.status_code == 200:
                dados = response.json()
                itinerarios = dados.get('itineraries', []) if isinstance(dados, dict) else dados
                
                if itinerarios and len(itinerarios) > 0:
                    print(f"✅ [ENGINE] {len(itinerarios)} opções encontradas!")
                    return processar_resultados(itinerarios)
                else:
                    print("⏳ [ENGINE] Aguardando processamento...")
            
            time.sleep(5)
        except Exception as e:
            print(f"❌ Erro no polling: {e}")
            break
            
    return []