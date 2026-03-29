import requests
import time
from scraper import obter_token_sessao 

# Configuração de Headers para simular navegador real na API de Poll
HEADERS_AUDITORIA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Origin': 'https://bestflightsprices.com',
    'Referer': 'https://bestflightsprices.com/',
    'Accept': 'application/json, text/plain, */*'
}

def obter_cotacoes():
    """Busca cotações em tempo real para converter moedas internacionais."""
    try:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,GBP-BRL"
        res = requests.get(url, timeout=5).json()
        return {
            'USD': float(res['USDBRL']['bid']), 
            'EUR': float(res['EURBRL']['bid']),
            'GBP': float(res['GBPBRL']['bid']),
            'BRL': 1.0
        }
    except:
        # Fallback caso a API de câmbio falhe
        return {'USD': 5.85, 'EUR': 6.30, 'GBP': 7.50, 'BRL': 1.0}

def processar_dados(itinerarios, pax):
    """Processa a lista de voos bruta da API e limpa para o Dashboard."""
    taxas = obter_cotacoes()
    pre_resultados = []
    pax_int = max(1, int(pax))
    
    for item in itinerarios:
        try:
            if not item.get('bestPrice'): continue
            
            # 1. Conversão Monetária
            moeda = item.get('currencyCode', 'USD')
            valor_raw = float(item.get('bestPrice', 0))
            if valor_raw > 100000: valor_raw /= 1000 
            
            cotacao = taxas.get(moeda, taxas.get('USD'))
            preco_total_brl = valor_raw * cotacao
            
            # 2. Divisão por Passageiro (Crucial para o Sniper)
            preco_por_pessoa = preco_total_brl / pax_int

            # 3. Funções Auxiliares de Extração (Evitando Fuso e Erro de Escalas)
            def extrair_data(f):
                if not f: return "---"
                dt = f.get('departureDateTime') or f.get('segments', [{}])[0].get('departureDateTime', {})
                if not dt: return "---"
                # Extração nominal (literal) evita que o dia mude por causa do timezone
                return f"{dt.get('day', 0):02d}/{dt.get('month', 0):02d}/{dt.get('year')}"

            def extrair_hora_fuso(f):
                if not f: return "---"
                dt = f.get('departureDateTime') or f.get('segments', [{}])[0].get('departureDateTime', {})
                if not dt: return "---"
                hora = f"{dt.get('hour', 0):02d}:{dt.get('minute', 0):02d}"
                offset = dt.get('offset')
                fuso = f" (UTC{'+' if offset >= 0 else ''}{offset})" if offset is not None else " (Local)"
                return f"{hora}{fuso}"

            def extrair_duracao_paradas(f):
                if not f: return "---", "Direto"
                
                # Conta segmentos para determinar paradas
                segments = f.get('segments', [])
                num_segments = len(segments)
                # Se houver 2 segmentos, houve 1 parada.
                stops = max(0, num_segments - 1)
                
                label = f"{stops} Parada(s)" if stops > 0 else "Direto"
                
                mins = f.get('durationInMinutes') or sum(s.get('durationInMinutes', 0) for s in segments)
                duracao = f"{mins // 60}h {mins % 60}m" if mins else "---"
                return duracao, label

            # 4. Estruturação dos Trechos
            v_ida = item.get('outboundFlight', {})
            v_volta = item.get('inboundFlight', {})

            dur_ida, stop_ida = extrair_duracao_paradas(v_ida)
            dur_volta, stop_volta = extrair_duracao_paradas(v_volta)

            pre_resultados.append({
                "valor_sort": preco_por_pessoa,           # Usado para ordenar e Sniper
                "valor_total_reserva": preco_total_brl,  # Usado para exibir o total no dashboard
                "pax_count": pax_int,
                "tipo": "RT" if (v_volta and v_volta.get('carrierName')) else "OW",
                "cia": v_ida.get('carrierName', '---'),
                "ida_data": extrair_data(v_ida),
                "ida_hora": extrair_hora_fuso(v_ida),
                "ida_duracao": dur_ida,
                "ida_paradas": stop_ida,
                "volta_data": extrair_data(v_volta),
                "volta_hora": extrair_hora_fuso(v_volta),
                "volta_duracao": dur_volta,
                "volta_paradas": stop_volta,
                "link": item.get('bookingLink')
            })
        except: continue

    # Ordenação: Menor preço unitário no topo
    ordenados = sorted(pre_resultados, key=lambda x: x['valor_sort'])
    
    for r in ordenados:
        # Formatações para exibição amigável no HTML
        r['preco_fmt'] = f"R$ {r['valor_sort']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        r['preco_total_fmt'] = f"R$ {r['valor_total_reserva']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return ordenados

def buscar_voos_completos(origem, destino, data_ida, data_volta, custo_milheiro, pax, classe):
    """Orquestra a captura do token e a busca dos resultados."""
    
    # ALTERAÇÃO OBRIGATÓRIA: Enviando 'pax' para o Scraper capturar o preço do grupo
    token = obter_token_sessao(origem, destino, data_ida, data_volta, classe, pax)
    
    if not token: 
        print("⚠️ [ENGINE] Falha ao obter token de sessão.")
        return []
    
    url_poll = f"https://sky-api-778236310566.us-central1.run.app/search/poll/{token}"
    
    # Loop de tentativas (Polling) para aguardar a API processar os resultados
    for i in range(15):
        try:
            res = requests.get(url_poll, headers=HEADERS_AUDITORIA, timeout=15)
            if res.status_code == 200:
                itins = res.json()
                if isinstance(itins, dict): 
                    itins = itins.get('itineraries', [])
                if itins: 
                    return processar_dados(itins, pax)
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ [ENGINE] Erro no polling: {e}")
            continue
            
    return []