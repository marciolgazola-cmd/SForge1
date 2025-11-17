import ollama
import json
import logging
from typing import List, Dict, Any, Optional
import pydantic # Necessário para usar .schema_json()

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Exceções personalizadas para tratamento mais granular
class LLMConnectionError(Exception):
    """Erro de conexão ou indisponibilidade do LLM."""
    pass

class LLMGenerationError(Exception):
    """Erro na geração de resposta pelo LLM (e.g., formato inválido, conteúdo vazio)."""
    pass

class LLMSimulator:
    """
    Simulador/Adaptador para interagir com o Ollama, suportando a geração de texto
    e JSON validado por Pydantic.
    """
    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._llm_available = False
        try:
            # Tenta uma conexão básica para verificar disponibilidade e o modelo
            logging.info(f"LLMSimulator: Tentando conectar ao Ollama em {base_url} com o modelo {model}...")
            # Usa um prompt simples para verificar a conexão
            ollama.chat(model=self.model, messages=[{'role': 'user', 'content': 'Hello'}], options={'num_predict': 1}, stream=False, base_url=self.base_url)
            logging.info(f"LLMSimulator: Ollama disponível e conectado ao {base_url} com o modelo {model}.")
            self._llm_available = True
        except ollama.ResponseError as e:
            logging.error(f"LLMSimulator: Erro de conexão com Ollama em {base_url} para o modelo {model}. Por favor, verifique se o Ollama está em execução e o modelo '{model}' está baixado (use 'ollama pull {model}'). Erro: {e}")
            self._llm_available = False
            # Não lança exceção aqui para permitir a inicialização, mas registra que o LLM não está disponível
        except Exception as e:
            logging.error(f"LLMSimulator: Erro inesperado ao inicializar Ollama. Erro: {e}")
            self._llm_available = False

    def chat(self, messages: List[Dict[str, str]], response_model=None, format_output: str = '') -> Any:
        """
        Envia uma requisição de chat ao Ollama.
        :param messages: Lista de mensagens no formato [{'role': 'user', 'content': '...'}]
        :param response_model: Modelo Pydantic para validar e parsear a resposta (se for JSON).
        :param format_output: 'json' para forçar a saída JSON, ou '' para texto padrão.
                              Se response_model for fornecido, format_output será sobrescrito para 'json'.
        :return: Conteúdo da resposta (string ou objeto Pydantic).
        :raises LLMConnectionError: Se houver problemas de conexão com o Ollama.
        :raises LLMGenerationError: Se a resposta do LLM for inválida ou não puder ser parseada.
        """
        if not self._llm_available:
            raise LLMConnectionError("Ollama não está disponível. Verifique os logs de inicialização para mais detalhes.")

        # Criamos uma cópia das mensagens para evitar modificações indesejadas no objeto original
        messages_to_send = [msg.copy() for msg in messages]

        try:
            current_format = format_output # Usa o formato passado, se houver
            if response_model:
                current_format = 'json' 
                # Adiciona instrução ao prompt para garantir que o LLM retorne JSON
                if messages_to_send and messages_to_send[-1]['role'] == 'user':
                    messages_to_send[-1]['content'] += f"\n\nRetorne a resposta EXCLUSIVAMENTE em formato JSON, aderindo estritamente ao seguinte esquema Pydantic: {response_model.schema_json(indent=2)}"
                else:
                    messages_to_send.append({'role': 'system', 'content': f"Você deve retornar sua resposta EXCLUSIVAMENTE em formato JSON, aderindo estritamente ao seguinte esquema Pydantic: {response_model.schema_json(indent=2)}"})

            options = {} # Pode ser expandido para outras opções do Ollama, se necessário

            response = ollama.chat(
                model=self.model,
                messages=messages_to_send, # Usa a cópia modificada
                stream=False,
                options=options,
                format=current_format, # Usa o formato determinado
                base_url=self.base_url
            )
            
            content = response['message']['content']
            if not content:
                raise LLMGenerationError("Resposta vazia ou nula do Ollama.")
            
            if response_model:
                try:
                    # Tenta parsear a resposta como JSON e validá-la com o modelo Pydantic
                    json_start = content.find('{')
                    json_end = content.rfind('}')
                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        json_str = content[json_start : json_end + 1]
                        parsed_content = response_model.parse_raw(json_str)
                        return parsed_content
                    else:
                        raise json.JSONDecodeError("Conteúdo não contém um JSON válido.", content, 0)
                except (json.JSONDecodeError, pydantic.ValidationError) as e:
                    logging.error(f"LLMGenerationError: Resposta do Ollama não é um JSON válido ou não valida com o modelo Pydantic. Erro: {e}\nConteúdo recebido: {content}")
                    raise LLMGenerationError(f"Resposta do Ollama não é um JSON válido ou não valida com o modelo Pydantic. Erro: {e}\nConteúdo recebido: {content}")
                except Exception as e:
                    logging.error(f"LLMGenerationError: Falha inesperada ao parsear a resposta do LLM com o modelo Pydantic. Erro: {e}\nConteúdo recebido: {content}")
                    raise LLMGenerationError(f"Falha inesperada ao parsear a resposta do LLM com o modelo Pydantic. Erro: {e}\nConteúdo recebido: {content}")
            else:
                return content
        except ollama.ResponseError as e:
            logging.error(f"LLMConnectionError: Erro de resposta do Ollama (código {e.status_code}). Verifique a conexão, se o modelo '{self.model}' está baixado (ollama pull {self.model}) ou se o prompt está correto. Erro: {e}")
            raise LLMConnectionError(f"Erro de resposta do Ollama: {e}")
        except LLMConnectionError: # Re-raise if already an LLMConnectionError from availability check
            raise
        except Exception as e:
            # Captura outros erros inesperados durante a chamada ao Ollama
            last_prompt_content = messages_to_send[-1]['content'] if messages_to_send else "N/A"
            logging.error(f"LLMGenerationError: Erro inesperado ao chamar Ollama. Erro: {e}. Último prompt enviado: '{last_prompt_content}'")
            raise LLMGenerationError(f"Erro inesperado ao chamar Ollama. Erro: {e}")