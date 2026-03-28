import requests
import time
from scraper import obter_token_sessao 

def obter_cotacoes_atuais():
    try:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,GBP-BRL"
        res = requests.get(url, timeout=5).json()
        return {'USD': float(res['USDBRL']['bid']), 'EUR': float(res['EURBRL']['bid']), 'BRL': 1.0}
    except:
        return {'USD': 5.25, 'EUR': 5.60, 'BRL': 1.0}

def processar_resultados(itinerarios, custo_milheiro=17.50, pax=1):
    taxas = obter_cotacoes_atuais()
    resultados = []
    
    # Filtra itinerários válidos
    itinerarios_validos = [it for it in itinerarios if it.get('bestPrice')]
    # Ordena pelo melhor preço
    itins_ordenados = sorted(itinerarios_validos, key=lambda x: x.get('bestPrice', 999999))

    for item in itins_ordenados:
        try:
            moeda = item.get('currencyCode', 'USD')
            # Preço vem em formato inteiro (ex: 500000 para 500.00)
            preco_raw = float(item.get('bestPrice')) / 1000
            total_brl = preco_raw * taxas.get(moeda, taxas.get('USD', 5.25))
            
            # Formatação R$ para exibição
            preco_str = f"R$ {total_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            # Cálculo Sniper por pessoa
            preco_por_pessoa = total_brl / pax
            # Arbitragem: Preço pagante vs Custo de emissão (considerando taxa média de R$ 410)
            limite_milhas = int((preco_por_pessoa - 410) / (custo_milheiro / 1000))
            
            status, cor = "⚠️ CILADA", "text-warning"
            if limite_milhas > 90000: status, cor = "🔥 OPORTUNIDADE", "text-danger"
            elif limite_milhas > 45000: status, cor = "✅ JUSTO", "text-success"

            def extrair_trecho(flight, sentido):
                dt = flight.get('departureDateTime', {})
                return {
                    "sentido": sentido,
                    "voo": flight.get('carrierName', '---'),
                    "trecho": f"{flight.get('departureAirport')} ➔ {flight.get('arrivalAirport')}",
                    "data": f"{dt.get('day', 0):02d}/{dt.get('month', 0):02d}/{dt.get('year', 0)} (GMT)",
                    "horario": f"{dt.get('hour', 0):02d}:{dt.get('minute', 0):02d}",
                    "preco": preco_str,
                    "status_sniper": status,
                    "classe_cor": cor,
                    "link": item.get('bookingLink')
                }

            if item.get('outboundFlight'): 
                resultados.append(extrair_trecho(item['outboundFlight'], "IDA"))
            if item.get('inboundFlight'): 
                resultados.append(extrair_trecho(item['inboundFlight'], "VOLTA"))
        except Exception as e:
            print(f"DEBUG: Erro ao processar itinerário: {e}")
            continue
    return resultados

def buscar_voos_completos(origem, destino, data_ida, data_volta=None, custo_milheiro=17.50, pax=1, classe='economy'):
    token = obter_token_sessao(origem, destino, data_ida, data_volta)
    if not token: 
        print("❌ [ENGINE] Falha ao obter Token de Sessão.")
        return []
    
    url = f"https://sky-api-778236310566.us-central1.run.app/search/poll/{token}"
    print(f"📡 [ENGINE] Consultando API com Token: {token[:15]}...")
    
    for tentativa in range(15):
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                dados = res.json()
                # A API pode retornar o dicionário direto ou uma lista
                itins = dados.get('itineraries', []) if isinstance(dados, dict) else dados
                if itins: 
                    print(f"✅ [ENGINE] {len(itins)} itinerários encontrados!")
                    return processar_resultados(itins, custo_milheiro, pax)
            
            print(f"⏳ [ENGINE] Aguardando resultados da API... ({tentativa+1}/15)")
        except Exception as e: 
            print(f"⚠️ [ENGINE] Erro na consulta: {e}")
        
        time.sleep(4)
    return []