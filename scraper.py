from playwright.sync_api import sync_playwright

def obter_token_sessao(origem, destino, data_ida, data_volta=None):
    # Trata data_volta se vier como string vazia do formulário
    if not data_volta or data_volta.strip() == "":
        url = f"https://bestflightsprices.com/pt/{origem}-{destino}/{data_ida}"
    else:
        url = f"https://bestflightsprices.com/pt/{origem}-{destino}/{data_ida}/{data_volta}"
    
    print(f"🔍 [SCRAPER] Iniciando captura em: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Bloqueia recursos pesados para ganhar velocidade
        page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,pdf}", lambda route: route.abort())

        try:
            # wait_until="commit" é mais rápido para pegar o início do redirecionamento
            page.goto(url, wait_until="commit", timeout=30000)

            token = None
            for i in range(25):  # Aumentado levemente o tempo de espera
                url_atual = page.url
                
                # Procura por diferentes padrões de token na URL
                if "sessionToken=" in url_atual:
                    token = url_atual.split("sessionToken=")[1].split("&")[0]
                    break
                elif "sessionID=" in url_atual:
                    token = url_atual.split("sessionID=")[1].split("&")[0]
                    break
                elif "sT=" in url_atual: # Padrão curto às vezes usado
                    token = url_atual.split("sT=")[1].split("&")[0]
                    break
                
                page.wait_for_timeout(1000)
                if i % 5 == 0 and i > 0:
                    print(f"📡 [SCRAPER] Aguardando redirecionamento... ({i}s)")

            if token:
                # Limpa caracteres de escape da URL
                token = token.replace("%3D%3D", "==").replace("%2F", "/").split('--')[0]
                print(f"✅ [SCRAPER] Token capturado: {token[:20]}...")
                return token
            
            print("⚠️ [SCRAPER] Timeout: Token não encontrado na URL.")
            return None
        except Exception as e:
            print(f"⚠️ [SCRAPER] Erro na navegação: {e}")
            return None
        finally:
            browser.close()