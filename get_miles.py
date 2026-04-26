import os
import json
import time
from playwright.sync_api import sync_playwright

def get_miles_data(origem, destino, data_ida):
    """
    VERSÃO REFINADA
    Ajuste: Filtro rigoroso para capturar o nome da CIA e ignorar campos de tempo (Last Seen).
    """
    with sync_playwright() as p:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        
        try:
            browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled']) 
            context = browser.new_context(user_agent=ua)
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            resgate_bruto = []

            def handle_response(response):
                url = response.url.lower()
                if ("_api/" in url or "search" in url) and response.status == 200:
                    try:
                        if "application/json" in response.headers.get("content-type", ""):
                            data = response.json()
                            availabilities = data.get('data') or data.get('availabilities') or []
                            if availabilities:
                                resgate_bruto.extend(availabilities)
                    except: pass

            page.on("response", handle_response)

            print(f"🌍 [GET_MILES] Buscando: {origem} -> {destino}")
            url_direta = f"https://seats.aero/search?date={data_ida}&origins={origem.upper()}&destinations={destino.upper()}"
            page.goto(url_direta, wait_until="domcontentloaded")
            
            # --- SCROLL PARA CARREGAR RESULTADOS ---
            print("⏳ [GET_MILES] Carregando voos e limpando dados...")
            for _ in range(6): 
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(1500)

            # VARREDURA PROFUNDA (DOM) - MELHORADA
            if not resgate_bruto:
                dom_data = page.evaluate(f"""() => {{
                    const items = [];
                    // Captura as linhas da tabela
                    const rows = Array.from(document.querySelectorAll('tr, [role="row"]')).slice(1);
                    
                    rows.forEach(row => {{
                        const cells = Array.from(row.querySelectorAll('td, [role="cell"]'));
                        if (cells.length >= 5) {{
                            const textos = cells.map(c => c.innerText.trim());
                            
                            // Lógica refinada para Nome da Cia:
                            // Ignora datas, termos de tempo (ago, now, just) e textos curtos demais
                            let nomeCia = textos.find(t => 
                                t.length > 2 && 
                                !t.includes('202') && 
                                !t.toLowerCase().includes('ago') && 
                                !t.toLowerCase().includes('now') &&
                                !t.toLowerCase().includes('just') &&
                                !t.toLowerCase().includes('minute')
                            ) || "Cia Desconhecida";

                            // Limpa quebras de linha e pega apenas a primeira parte (o nome real)
                            nomeCia = nomeCia.split('\\n')[0].trim();

                            // Captura milhas (procura o primeiro número grande que não seja o ano)
                            let milhas = textos.map(t => parseInt(t.replace(/\\D/g, '')))
                                               .find(n => n > 2000 && n < 1000000) || 0;

                            if (milhas > 0) {{
                                items.push({{ "EconomyPoints": milhas, "Airlines": nomeCia }});
                            }}
                        }}
                    }});
                    return items;
                }}""")
                if dom_data: resgate_bruto = dom_data

            # Limpeza final e formatação para o Dashboard
            vistos = set()
            resultado_final = []
            for voo in resgate_bruto:
                # Normalização dos campos vindos da API ou do DOM
                p = voo.get('EconomyPoints') or voo.get('points', 0)
                c = voo.get('Airlines') or 'Cia'
                
                # Evitar duplicatas exatas de Cia e Valor na mesma busca
                chave = f"{c}-{p}".lower()
                if p > 0 and chave not in vistos:
                    vistos.add(chave)
                    resultado_final.append({
                        "EconomyPoints": p,
                        "TaxAmount": 15, # Valor base para cálculo do CPM
                        "Airlines": c,
                        "OriginIata": origem.upper(),
                        "DestinationIata": destino.upper(),
                        "Date": data_ida
                    })

            print(f"✅ [GET_MILES] Finalizado com {len(resultado_final)} voos auditados.")
            return resultado_final if resultado_final else None

        except Exception as e:
            print(f"❌ [GET_MILES] Erro no Scraper: {e}")
            return None
        finally:
            if 'browser' in locals():
                browser.close()