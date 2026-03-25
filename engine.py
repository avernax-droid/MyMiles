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
            # Ajuste de escala baseado no F12: 1419000 -> 141.900 pts
            raw_price = int(item.get('bestPrice', 0))
            valor_milhas = int(raw_price / 10) 
            preco_display = f"{valor_milhas:,} pts".replace(",", ".")

            # --- TAXAS DE EMBARQUE (RASTREADOR AGRESSIVO) ---
            # O Python testará cada uma destas chaves até encontrar um valor maior que zero.
            # Isso cobre variações entre GOL, LATAM e outras Cias no JSON do site.
            raw_tax = (
                item.get('totalTaxes') or 
                item.get('priceDetail', {}).get('totalTaxes') or 
                item.get('priceDetail', {}).get('taxes') or 
                item.get('fare', {}).get('taxes') or 
                item.get('fare', {}).get('totalTaxes') or 0
            )

            if raw_tax > 0:
                # Conforme análise F12, taxas em centavos: 54500 -> R$ 545,00
                taxa_reais = float(raw_tax) / 100
                taxa_display = f"R$ {taxa_reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                # Caso o JSON realmente venha zerado em todas as chaves mapeadas
                taxa_display = "Ver no Link"

            def limpar_trecho(flight, sentido, preco_info, taxa_info):
                # Localização correta do horário e escalas (F12)
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
                # Na IDA mostramos o total de milhas e taxas do pacote
                voos_formatados.append(limpar_trecho(out, "IDA", preco_display, taxa_display))
            if inb and inb.get('departureAirport'):
                # Na VOLTA, mantemos limpo para não confundir o valor total
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

    # PRESERVADO: Polling de 12 tentativas (60s total) para rotas internacionais
    for i in range(12):
        print(f"📡 [ENGINE] Polling Sky-API ({i+1}/12)...")
        try:
            response = requests.get(url_api, headers=headers, timeout=30)
            if response.status_code == 200:
                dados = response.json()
                # Tratamento para JSON vir como Lista ou Dicionário conforme seu F12
                itinerarios = dados.get('itineraries', []) if isinstance(dados, dict) else dados
                
                if itinerarios and len(itinerarios) > 0:
                    print(f"✅ [ENGINE] {len(itinerarios)} opções encontradas!")
                    return processar_resultados(itinerarios)
                else:
                    print("⏳ [ENGINE] Aguardando processamento dos voos no servidor...")
            
            time.sleep(5)
        except Exception as e:
            print(f"❌ Erro no polling: {e}")
            break
            
    return []