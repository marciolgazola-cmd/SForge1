import requests
import json
import os

class OllamaLLMInterface:
    def __init__(self, model_name: str = "mistral", ollama_base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.generate_endpoint = f"{self.ollama_base_url}/api/generate"
        print(f"OllamaLLMInterface inicializado para o modelo: {self.model_name} na URL: {self.ollama_base_url}")

    def generate_response(self, prompt: str, system_message: str = None) -> str:
        headers = {"Content-Type": "application/json"}
        
        # Estrutura do payload para o Ollama
        # Se tiver uma mensagem de sistema, inclua. Caso contrário, apenas o prompt.
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model_name,
            "prompt": prompt, # Para a API /api/generate, o prompt é o principal. messages é para /api/chat.
                             # Vamos manter a compatibilidade básica com generate, mas o ideal seria /api/chat
                             # para múltiplos turnos e system message. Para este primeiro momento,
                             # vamos usar o campo 'prompt' diretamente.
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_k": 40,
                "top_p": 0.9,
            }
        }
        
        print(f"Enviando prompt ao Ollama ({self.model_name}): {prompt[:200]}...") # Log para debug
        try:
            response = requests.post(self.generate_endpoint, headers=headers, json=data)
            response.raise_for_status() # Lança exceção para códigos de status HTTP de erro (4xx ou 5xx)
            
            response_json = response.json()
            
            # A API /api/generate retorna a resposta em 'response' ou 'message.content' (se for chat-like)
            # Para 'generate', normalmente está em 'response'.
            generated_text = response_json.get("response", "")
            
            print(f"Resposta do Ollama recebida: {generated_text[:200]}...") # Log para debug
            return generated_text

        except requests.exceptions.ConnectionError as e:
            print(f"Erro de conexão com o Ollama: {e}")
            print(f"Certifique-se de que o servidor Ollama está rodando em {self.ollama_base_url} e o modelo '{self.model_name}' está disponível.")
            return json.dumps({"error": f"Erro de conexão com o Ollama: {e}. Verifique se 'ollama serve' está rodando e o modelo '{self.model_name}' está baixado."})
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição Ollama: {e}")
            return json.dumps({"error": f"Erro na requisição Ollama: {e}"})
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON da resposta do Ollama: {e}")
            print(f"Resposta bruta: {response.text}")
            return json.dumps({"error": f"Erro ao decodificar JSON da resposta do Ollama: {e}. Resposta bruta: {response.text}"})
        except Exception as e:
            print(f"Erro inesperado ao interagir com Ollama: {e}")
            return json.dumps({"error": f"Erro inesperado ao interagir com Ollama: {e}"})

# Exemplo de uso (pode ser útil para testes rápidos)
if __name__ == "__main__":
    # Certifique-se de que 'ollama serve' está rodando em um terminal separado
    # e que o modelo 'mistral' está baixado (ollama pull mistral)
    
    ollama_interface = OllamaLLMInterface(model_name="mistral")
    
    test_prompt = "Me dê uma breve descrição do que é um agente de IA."
    print("\n--- Teste 1: Prompt Simples ---")
    response_simple = ollama_interface.generate_response(test_prompt)
    print(f"Resposta: {response_simple}")

    test_prompt_json = 'Gere um JSON com o nome "projeto" e o valor "Synapse Forge".'
    print("\n--- Teste 2: Prompt para JSON ---")
    response_json = ollama_interface.generate_response(test_prompt_json)
    print(f"Resposta JSON: {response_json}")

    test_system_message = "Você é um assistente útil e conciso. Responda em uma frase."
    test_prompt_with_system = "Qual a capital da França?"
    print("\n--- Teste 3: Prompt com System Message (usando /api/generate) ---")
    # Nota: A API /api/generate do Ollama trata a system message de forma limitada
    # quando não é a API /api/chat. Para prompts simples, o system message pode
    # ser incorporado ao prompt principal se necessário.
    # Por enquanto, estamos usando o prompt direto para /api/generate.
    # Podemos adaptar para /api/chat posteriormente se necessário.
    response_with_system = ollama_interface.generate_response(
        f"{test_system_message}\n\n{test_prompt_with_system}"
    )
    print(f"Resposta com System Message: {response_with_system}")