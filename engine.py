import requests
import time
from scraper import obter_token_sessao 

HEADERS_AUDITORIA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Origin': 'https://bestflightsprices.com',
    'Referer': 'https://bestflightsprices.com/',
    'Accept': 'application/json, text/plain, */*'
}

def obter_cotacoes():
    try:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL"
        res = requests.get(url, timeout=5).json()
        return {'USD': float(res['USDBRL']['bid']), 'EUR': float(res['EURBRL']['bid']), 'BRL': 1.0}
    except:
        return {'USD': 5.30, 'EUR': 5.70, 'BRL': 1.0}

def processar_dados(itinerarios, custo_milheiro, pax):
    taxas = obter_cotacoes()
    resultados = []
    
    itins = [i for i in itinerarios if i.get('bestPrice')]
    itins = sorted(itins, key=lambda x: x.get('bestPrice', 999999))

    for item in itins:
        try:
            moeda = item.get('currencyCode', 'USD')
            # O bestPrice da API costuma ser o total do itinerário
            valor_raw = float(item.get('bestPrice')) / 1000
            total_brl = valor_raw * taxas.get(moeda, taxas.get('USD', 5.30))
            
            # NORMALIZAÇÃO: Dividimos pelo número de passageiros para auditoria unitária
            preco_por_pessoa = total_brl / pax
            preco_formatado = f"R$ {preco_por_pessoa:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            def formatar_voo(flight, sentido):
                if not flight: return None
                dt = flight.get('departureDateTime', {})
                
                # Correção de Escalas (Evita o -1)
                segmentos = flight.get('segments', [])
                n_seg = len(segmentos)
                txt_escalas = "Direto" if n_seg <= 1 else f"{n_seg - 1} Escala(s)"
                
                classes = {"ECONOMY": "Econômica", "BUSINESS": "Executiva", "FIRST": "Primeira"}
                classe_slug = flight.get('cabinClass', 'ECONOMY')
                
                return {
                    "sentido": sentido,
                    "voo": flight.get('carrierName', '---'),
                    "data": f"{dt.get('day', 0):02d}/{dt.get('month', 0):02d}/{dt.get('year')}",
                    "horario": f"{dt.get('hour', 0):02d}:{dt.get('minute', 0):02d}",
                    "classe": classes.get(classe_slug, classe_slug),
                    "escalas": txt_escalas,
                    "preco": preco_formatado,
                    "link": item.get('bookingLink')
                }

            if item.get('outboundFlight'): 
                resultados.append(formatar_voo(item['outboundFlight'], "IDA"))
            if item.get('inboundFlight'): 
                resultados.append(formatar_voo(item['inboundFlight'], "VOLTA"))
        except: 
            continue
    return resultados

def buscar_voos_completos(origem, destino, data_ida, data_volta, custo_milheiro, pax, classe):
    token = obter_token_sessao(origem, destino, data_ida, data_volta, classe)
    if not token: return []
    
    url_poll = f"https://sky-api-778236310566.us-central1.run.app/search/poll/{token}"
    
    for i in range(20):
        try:
            response = requests.get(url_poll, headers=HEADERS_AUDITORIA, timeout=15)
            if response.status_code == 200:
                dados = response.json()
                itins = []
                if isinstance(dados, list): itins = dados
                elif isinstance(dados, dict): itins = dados.get('itineraries', [])
                
                if itins and len(itins) > 0:
                    return processar_dados(itins, custo_milheiro, pax)
            print(f"⏳ [ENGINE] Sincronizando tarifas ({classe})... ({i+1}/20)")
        except: 
            pass
        time.sleep(3)
    return []