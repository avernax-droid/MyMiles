from playwright.sync_api import sync_playwright

def obter_token_sessao(origem, destino, data_ida, data_volta=None, classe="ECONOMY", pax=1):
    """
    Captura o token de sessão interceptando a requisição de 'poll' do site original.
    Inclui PAX e CLASSE na URL para garantir que o preço retornado seja condizente com a busca.
    """
    
    # 1. Montagem da URL com os parâmetros de passageiros e classe
    url_base = f"https://bestflightsprices.com/pt/{origem}-{destino}/{data_ida}"
    if data_volta and data_volta.strip():
        url_base += f"/{data_volta}"
    
    # Adicionamos cabinClass e adults para o site carregar o contexto correto
    url_final = f"{url_base}?cabinClass={classe}&adults={pax}"
    
    print(f"🔍 [SCRAPER] Interceptando tráfego em: {url_final} (PAX: {pax})")
    
    with sync_playwright() as p:
        # Launch com argumentos de performance para ambientes Docker/WSL
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()

        token_capturado = {"token": None}

        # Função de interceptação de rede
        def handle_request(request):
            if "search/poll/" in request.url:
                try:
                    # O token costuma ser a parte da URL após 'poll/' e antes de qualquer '?'
                    token = request.url.split("poll/")[1].split("?")[0]
                    token_capturado["token"] = token
                except:
                    pass

        # Registra o listener de requisições
        page.on("request", handle_request)

        try:
            # Bloqueio de mídias para economizar banda e tempo
            page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
            
            # Navega até a página. 'commit' é mais rápido que 'networkidle' para capturar o primeiro poll
            page.goto(url_final, wait_until="commit", timeout=45000)

            # Aguarda até que o token seja capturado ou atinja o timeout de 15 segundos
            for _ in range(15):
                if token_capturado["token"]: 
                    break
                page.wait_for_timeout(1000)

            if token_capturado["token"]:
                # Limpa o token de codificações de URL comuns que quebram a API posterior
                token_limpo = token_capturado["token"].replace("%3D", "=").replace("%2F", "/")
                print(f"✅ [SCRAPER] Token capturado com sucesso para {pax} PAX.")
                return token_limpo
            
            print("⚠️ [SCRAPER] Erro: Token não encontrado no tempo limite.")
            return None

        except Exception as e:
            print(f"⚠️ [SCRAPER] Erro durante a execução: {e}")
            return None
        finally:
            browser.close()