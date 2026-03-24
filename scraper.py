from playwright.sync_api import sync_playwright
import time

def obter_token_sessao(origem, destino):
    """
    Navega até o site e captura o token de sessão (Token ou ID) na URL.
    """
    # URL de busca padrão (Data fixa para teste, pode ser parametrizada depois)
    url = f"https://bestflightsprices.com/pt/{origem}-{destino}/2026-06-10/2026-06-17"
    
    print(f"🔍 [SCRAPER] Acessando: {url}")
    
    with sync_playwright() as p:
        # headless=True para não abrir a janela do Chrome no WSL
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("⏳ [SCRAPER] Carregando página...")
            # Usamos 'domcontentloaded' para ser mais rápido que o carregamento total
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            # Aguarda o redirecionamento do Next.js onde o token aparece na URL
            page.wait_for_timeout(7000) 

            url_atual = page.url
            print(f"🔗 [SCRAPER] URL final: {url_atual[:110]}...")

            token = None
            # Suporta os dois padrões de nome que o site utiliza
            if "sessionToken=" in url_atual:
                token = url_atual.split("sessionToken=")[1].split("&")[0]
            elif "sessionID=" in url_atual:
                token = url_atual.split("sessionID=")[1].split("&")[0]

            if token:
                print(f"✅ [SCRAPER] Token detectado com sucesso!")
                return token
            else:
                print("❌ [SCRAPER] Falha ao extrair token da URL.")
                return None

        except Exception as e:
            print(f"❌ [SCRAPER] Erro no Playwright: {e}")
            return None
        finally:
            browser.close()

if __name__ == "__main__":
    # Teste rápido via terminal: python3 scraper.py
    resultado = obter_token_sessao("GRU", "EZE")
    print(f"\n--- TESTE DO SCRAPER ---\nToken capturado: {resultado}")