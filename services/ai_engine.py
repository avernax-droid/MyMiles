import google.generativeai as genai
import json
import logging
import re

class AIEngine:
    def __init__(self, api_key):
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logging.info("🧠 AIEngine: Pronto.")
        except Exception as e:
            logging.error(f"❌ Erro Gemini: {e}")

    def extrair_dados_voo(self, texto_bruto):
        # Se o Playwright falhou, não gastamos ficha de API
        if not texto_bruto or len(texto_bruto) < 800:
            return {"voos": []}

        prompt = f"""
        Aja como um extrator de dados. No texto abaixo, ignore avisos de cookies e extraia voos da LATAM em milhas.
        Retorne APENAS JSON: {{"voos": [{{"cia": "LATAM", "voo": "LA123", "trecho": "GRU-MIA", "milhas": 50000, "taxas": 200.00}}]}}
        TEXTO: {texto_bruto[:15000]}
        """

        try:
            response = self.model.generate_content(prompt)
            match = re.search(r'(\{.*\})', response.text, re.DOTALL)
            return json.loads(match.group(1)) if match else {"voos": []}
        except:
            return {"voos": []}