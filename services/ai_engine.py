<<<<<<< HEAD
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
=======
import logging
import json
import os
import hashlib
import time
from google import genai

class AIEngine:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.cache_file = 'cache_voos.json'
        
        # USANDO O NOME EXATO DA SUA LISTA (Focado em velocidade)
        self.model_id = "models/gemini-flash-latest" 
        
        self._carregar_cache()
        logging.info(f"AIEngine inicializado com sucesso. Modelo: {self.model_id}")

    def _carregar_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}
        else:
            self.cache = {}

    def _salvar_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Erro ao salvar cache: {e}")

    def _gerar_hash(self, texto):
        return hashlib.md5(texto.strip().lower().encode()).hexdigest()

    def extrair_dados_voo(self, texto_bruto: str, max_tentativas=2):
        texto_hash = self._gerar_hash(texto_bruto)
        if texto_hash in self.cache:
            logging.info("Cache: Retornando dados salvos.")
            return self.cache[texto_hash]

        # Prompt otimizado para a série 2.0/2.5
        prompt_completo = (
            "Extraia os voos do texto abaixo e retorne APENAS um JSON puro.\n"
            "Formato: {'voos': [{'cia': str, 'milhas': int, 'taxas': float, 'trecho': str, 'voo': str}]}\n\n"
            f"TEXTO: {texto_bruto}"
        )

        for tentativa in range(max_tentativas):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt_completo
                )
                
                if not response or not response.text:
                    continue

                # Limpa o Markdown
                txt_limpo = response.text.replace('```json', '').replace('```', '').strip()
                resultado = json.loads(txt_limpo)
                
                if "voos" in resultado:
                    self.cache[texto_hash] = resultado
                    self._salvar_cache()
                    return resultado
                
            except Exception as e:
                logging.warning(f"Tentativa {tentativa + 1} falhou: {e}")
                time.sleep(1)
                continue

        return {"voos": []}
>>>>>>> d10e5449e13c53935bbe0eba624404f25bc0ee3f
