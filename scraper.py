from playwright.sync_api import sync_playwright

def obter_token_sessao(origem, destino, data_ida, data_volta=None, classe="ECONOMY"):
    # Montagem da URL incluindo a classe selecionada pelo usuário
    url_base = f"https://bestflightsprices.com/pt/{origem}-{destino}/{data_ida}"
    if data_volta and data_volta.strip():
        url_base += f"/{data_volta}"
    
    # Adiciona o parâmetro de classe para garantir que o token seja da categoria correta
    url_final = f"{url_base}?cabinClass={classe}"
    
    print(f"🔍 [SCRAPER] Interceptando tráfego em: {url_final}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        token_capturado = {"token": None}

        def handle_request(request):
            if "search/poll/" in request.url:
                try:
                    token = request.url.split("poll/")[1].split("?")[0]
                    token_capturado["token"] = token
                except: pass

        page.on("request", handle_request)

        try:
            # Bloqueio de mídia para performance
            page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
            
            # domcontentloaded para evitar timeout de scripts de terceiros
            page.goto(url_final, wait_until="domcontentloaded", timeout=45000)

            for _ in range(15):
                if token_capturado["token"]: break
                page.wait_for_timeout(1000)

            if token_capturado["token"]:
                token = token_capturado["token"].replace("%3D%3D", "==").replace("%2F", "/")
                print(f"✅ [SCRAPER] Token capturado para classe {classe}.")
                return token
            return None
        except Exception as e:
            print(f"⚠️ [SCRAPER] Erro: {e}")
            return None
        finally:
            browser.close()