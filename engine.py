import requests
import json
import time

# Importação da função do scraper.py
try:
    from scraper import obter_token_sessao
except ImportError as e:
    print(f"❌ Erro de Importação: Verifique se scraper.py existe! {e}")

def buscar_voos_completos(origem, destino):
    print(f"\n--- 🔍 Iniciando Engine: {origem} -> {destino} ---")
    
    # 1. OBTÉM O TOKEN VIA SCRAPER
    token_bruto = obter_token_sessao(origem, destino)
    
    if not token_bruto:
        print("❌ ERRO: O Scraper não conseguiu gerar um token válido.")
        return []

    # 2. PREPARAÇÃO DO POLLING (Consulta à API real)
    token_limpo = token_bruto.split('--')[0]
    url_poll = f"https://sky-api-778236310566.us-central1.run.app/search/poll/{token_limpo}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://bestflightsprices.com",
        "Referer": "https://bestflightsprices.com/"
    }

    # 3. POLLING (Tenta 3 vezes até a API processar os voos)
    itinerarios = []
    for tentativa in range(1, 4):
        try:
            print(f"📡 [ENGINE] Consultando API (Tentativa {tentativa}/3)...")
            response = requests.get(url_poll, headers=headers, timeout=25)
            
            if response.status_code == 200:
                dados_brutos = response.json()
                itinerarios = dados_brutos.get('itineraries', [])
                if itinerarios:
                    print(f"✅ Sucesso: {len(itinerarios)} itinerários encontrados.")
                    break
                time.sleep(3)
            else:
                print(f"⚠️ API retornou status: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ Falha na conexão API: {e}")
            break

    return processar_resultados(itinerarios) if itinerarios else []

def processar_resultados(itinerarios):
    voos_formatados = []
    
    for item in itinerarios:
        try:
            # Pega os trechos (outbound = ida, inbound = volta)
            outbound = item.get('outboundFlight') or item.get('outbound', {})
            inbound = item.get('inboundFlight') or item.get('inbound', {})
            
            # --- LÓGICA DE PREÇOS E TAXAS ---
            preco_bruto = int(item.get('bestPrice', 0))
            taxas_brutas = item.get('totalTaxes') or item.get('taxes') or item.get('fees', 0)
            
            # Se o preço for muito alto, dividimos por 100 (centavos). 
            # Caso contrário, tratamos como o número de milhas.
            valor_milhas = int(preco_bruto / 100) if preco_bruto > 500000 else preco_bruto
            valor_taxas = float(taxas_brutas / 100) if float(taxas_brutas) > 1000 else float(taxas_brutas)

            def extrair_info(voo_obj):
                # Limpa horário (Ex: 2026-06-10T14:30:00 -> 14:30)
                saida_raw = voo_obj.get('departureTime') or voo_obj.get('departure_time') or 'Consulte'
                if 'T' in saida_raw:
                    saida_raw = saida_raw.split('T')[1][:5]
                
                cia = voo_obj.get('carrierName') or voo_obj.get('airline', 'LATAM')
                orig = voo_obj.get('departureAirport') or voo_obj.get('origin', '---')
                dest = voo_obj.get('arrivalAirport') or voo_obj.get('destination', '---')
                dur = voo_obj.get('durationInMinutes') or voo_obj.get('duration_minutes', 0)
                esc = voo_obj.get('stopCount', 0)
                
                return cia, orig, dest, saida_raw, dur, esc

            # Processa Trecho de IDA
            cia_i, orig_i, dest_i, hora_i, dur_i, esc_i = extrair_info(outbound)
            voos_formatados.append({
                "sentido": "IDA",
                "voo": cia_i,
                "origem": orig_i,
                "destino": dest_i,
                "saida": hora_i,
                "duracao": f"{dur_i} min" if dur_i > 0 else "Direto",
                "escalas": esc_i,
                "milhas": valor_milhas,
                "taxas": valor_taxas,
                "link": item.get('bookingLink', '#')
            })

            # Processa Trecho de VOLTA (se existir)
            if inbound and (inbound.get('departureAirport') or inbound.get('origin')):
                cia_v, orig_v, dest_v, hora_v, dur_v, esc_v = extrair_info(inbound)
                voos_formatados.append({
                    "sentido": "VOLTA",
                    "voo": cia_v,
                    "origem": orig_v,
                    "destino": dest_v,
                    "saida": hora_v,
                    "duracao": f"{dur_v} min" if dur_v > 0 else "Direto",
                    "escalas": esc_v,
                    "milhas": 0, # Preço consolidado na IDA
                    "taxas": 0.00,
                    "link": item.get('bookingLink', '#')
                })
        except Exception as e:
            print(f"⚠️ Erro ao processar item: {e}")
            continue

    return voos_formatados