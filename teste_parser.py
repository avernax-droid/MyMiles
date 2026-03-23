import json
from parser import extrair_voos_latam, extrair_voos_texto_bruto

def testar_leitura_json():
    print("--- Testando Leitura de JSON ---")
    # Usando o caminho que apareceu no seu git status: data/dadoslatam.json
    caminho = "data/dadoslatam.json"
    
    try:
        resultados = extrair_voos_latam(caminho)
        if resultados:
            print(f"✅ Sucesso! Encontrados {len(resultados)} voos no JSON.")
            for voo in resultados[:3]: # Mostra os 3 primeiros para não inundar o terminal
                print(f"   Voo: {voo['voo']} | {voo['origem']} -> {voo['destino']} | Milhas: {voo['milhas']} | Taxas: {voo['taxas']}")
        else:
            print("⚠️ O arquivo JSON foi lido, mas nenhum voo foi extraído. Verifique a estrutura 'content' -> 'summary'.")
    except FileNotFoundError:
        print(f"❌ Erro: O arquivo {caminho} não foi encontrado.")

def testar_leitura_texto():
    print("\n--- Testando Leitura de Texto Bruto (Regex) ---")
    texto_exemplo = """14:55\nGRU\nDuração\n16 h 40 min.\n6:35+1\nMIA\nPor pessoa a partir de\n55.000 milhas\n+ BRL 160,80"""
    
    resultados = extrair_voos_texto_bruto(texto_exemplo)
    if resultados:
        print(f"✅ Sucesso! Regex capturou {len(resultados)} voo(s) do texto.")
        v = resultados[0]
        print(f"   Dados: {v['origem']}->{v['destino']} | {v['milhas']} milhas | Taxas: R$ {v['taxas']}")
    else:
        print("❌ Erro: O Regex não conseguiu encontrar o padrão no texto de exemplo.")

if __name__ == "__main__":
    testar_leitura_json()
    testar_leitura_texto()
    