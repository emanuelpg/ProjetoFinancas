from dotenv import load_dotenv
load_dotenv()

from concurrent.futures import ThreadPoolExecutor, TimeoutError
import os
from google import genai
from google.genai import types

class Chat:
    prompt = "Liste os produtos e preços da seguinte forma, ex: Nome_produto / preço / Data (YYYY-MM-DD) / Categoria. " \
    "No preço coloque só o valor (sem simbolo, eg. R$ 2.57 => 2.57) nada mais nada menos, " \
    "além disso retire do nome do produto as informações de quantidade e/ou peso. Categoria deve ser dos tipos:" \
    "('Doce', 'Fruta', 'Comida Pronta', 'Comida para Fazer', 'Saúde', 'Higiene', 'Planejado', 'Transporte', 'Reserva'). " \
    "se não encontrar nenhum produto (i.e. n for imagem de uma compra), apenas informe explicitamente: NOT_FOUND"

    def __init__(self):
        self.client = genai.Client()
        self.models = self.getAvailableModels()
        self.models = ["gemini-flash-lite-latest"]

    def getModelAnswer(self, img, timeout_segundos=30):
        for m in self.models:
            try:
                print(f"Tentando modelo {m} (tempo limite: {timeout_segundos}s)...")

                # Configura timeout direto no cliente HTTP da biblioteca
                config = types.GenerateContentConfig(
                    http_options=types.HttpOptions(timeout=timeout_segundos * 1000)  # em ms
                )

                chat = self.client.chats.create(model=m, config=config)
                response = chat.send_message(message=[img, Chat.prompt])

                if response and response.text:
                    return response.text

            except Exception as e:
                pass
                print(f"Modelo {m} falhou ou expirou o tempo! Erro: {e}")
        return None


    def getAvailableModels(self):
        models = []
        #print("Modelos Disponíveis:")
        for model in self.client.models.list():
            if "generateContent" in model.supported_actions:
                #print(f"Display Name: {model.display_name}")
                #print("-" * 40)
                clean_name = model.name.replace("models/", "")
                models.append(clean_name)
        return models

    