# teste_engine.py
from engine import buscar_voos_completos

print("🚀 Iniciando teste de motor...")
resultados = buscar_voos_completos("GRU", "MIA")

if resultados:
    print(f"✅ Sucesso! Encontrados {len(resultados)} trechos.")
    for voo in resultados[:2]: # Mostra os 2 primeiros
        print(f"- {voo['voo']}: {voo['origem']} -> {voo['destino']} | Preço: {voo['milhas']}")
else:
    print("❌ Falha: Nenhum dado retornado. Verifique o scraper.py e a conexão.")
    