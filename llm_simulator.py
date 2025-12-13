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
    Simulador/Adaptador para interagir com o Ollama, suportando múltiplos modelos
    e a geração de texto validado por Pydantic.
    
    Modelos disponíveis e seus usos recomendados:
    - 'mistral': Modelo padrão versátil (AGP, ADO, ANP, AMS, AID, AAD)
    - 'llama3': Análise profunda e raciocínio (ARA, AQT, ASE)
    - 'codellama': Especializado em código (ADEX)
    """
    # Mapeamento de modelos para configurações otimizadas
    MODEL_CONFIGS = {
        'mistral': {
            'temperature': 0.5,
            'top_p': 0.85,
            'top_k': 50,
            'num_predict': 4096,
            'num_ctx': 8192,
            'repeat_penalty': 1.1,
        },
        'llama3': {
            'temperature': 0.3,  # Mais conservador para análise
            'top_p': 0.9,
            'top_k': 50,
            'num_predict': 4096,
            'num_ctx': 8192,
            'repeat_penalty': 1.0,
        },
        'codellama': {
            'temperature': 0.1,  # Muito conservador para código
            'top_p': 0.95,
            'top_k': 50,
            'num_predict': 8192,  # Mais tokens para código longo
            'num_ctx': 16384,     # Contexto maior para código
            'repeat_penalty': 1.0,
        }
    }

    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        self.model = model.lower()  # Ensure model is in lowercase for consistency
        self.base_url = base_url
        self._llm_available = False
        self._available_models = {}  # Cache de modelos disponíveis
        
        try:
            # Tenta uma conexão básica para verificar disponibilidade e o modelo
            logging.info(f"LLMSimulator: Tentando conectar ao Ollama em {base_url} com o modelo {self.model}...")
            # Usa um prompt simples para verificar a conexão (sem base_url, usa variável de ambiente)
            import os
            os.environ['OLLAMA_HOST'] = base_url
            ollama.chat(model=self.model, messages=[{'role': 'user', 'content': 'Hello'}], options={'num_predict': 1}, stream=False)
            logging.info(f"LLMSimulator: Ollama disponível e conectado ao {base_url} com o modelo {self.model}.")
            self._llm_available = True
        except ollama.ResponseError as e:
            logging.error(f"LLMSimulator: Erro de conexão com Ollama em {base_url} para o modelo {self.model}. Por favor, verifique se o Ollama está em execução e o modelo '{self.model}' está baixado (use 'ollama pull {self.model}'). Erro: {e}")
            self._llm_available = False
            # Não lança exceção aqui para permitir a inicialização, mas registra que o LLM não está disponível
        except Exception as e:
            logging.error(f"LLMSimulator: Erro inesperado ao inicializar Ollama. Erro: {e}")
            self._llm_available = False

    def set_model(self, model: str) -> None:
        """
        Muda o modelo LLM em tempo de execução.
        
        :param model: Nome do modelo ('mistral', 'llama3', 'codellama')
        :raises LLMConnectionError: Se o modelo não estiver disponível no Ollama
        """
        model_lower = model.lower()
        if model_lower == self.model:
            logging.info(f"LLMSimulator: Modelo já é {model_lower}.")
            return
        
        try:
            # Verifica se o modelo está disponível
            ollama.chat(model=model_lower, messages=[{'role': 'user', 'content': 'test'}], options={'num_predict': 1}, stream=False)
            self.model = model_lower
            logging.info(f"LLMSimulator: Modelo mudado para {model_lower}.")
        except ollama.ResponseError as e:
            error_msg = f"Modelo '{model}' não disponível no Ollama. Verifique com 'ollama list' ou execute 'ollama pull {model}'. Erro: {e}"
            logging.error(f"LLMSimulator: {error_msg}")
            raise LLMConnectionError(error_msg)

    def chat(self, messages: List[Dict[str, str]], response_model=None, format_output: str = '', model_override: str = None) -> Any:
        """
        Envia uma requisição de chat ao Ollama.
        :param messages: Lista de mensagens no formato [{'role': 'user', 'content': '...'}]
        :param response_model: Modelo Pydantic para validar e parsear a resposta (se for JSON).
        :param format_output: 'json' para forçar a saída JSON, ou '' para texto padrão.
                              Se response_model for fornecido, format_output será sobrescrito para 'json'.
        :param model_override: Se fornecido, usa este modelo em vez do padrão (e.g., 'codellama' para ADEX)
        :return: Conteúdo da resposta (string ou objeto Pydantic).
        :raises LLMConnectionError: Se houver problemas de conexão com o Ollama.
        :raises LLMGenerationError: Se a resposta do LLM for inválida ou não puder ser parseada.
        """
        if not self._llm_available:
            raise LLMConnectionError("Ollama não está disponível. Verifique os logs de inicialização para mais detalhes.")

        # Determina qual modelo usar
        current_model = model_override.lower() if model_override else self.model
        
        # Se há override, valida que o modelo está disponível
        if model_override and model_override.lower() != self.model:
            try:
                ollama.chat(model=current_model, messages=[{'role': 'user', 'content': 'test'}], options={'num_predict': 1}, stream=False)
            except Exception as e:
                logging.warning(f"LLMSimulator: Model override '{model_override}' não disponível, usando '{self.model}'. Erro: {e}")
                current_model = self.model

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

            # Obter configurações otimizadas para o modelo
            options = self.MODEL_CONFIGS.get(current_model, self.MODEL_CONFIGS['mistral']).copy()
            
            # Adicionar configurações adicionais (comuns a todos os modelos)
            options.update({
                'num_thread': 8,           # Threads CPU (Ryzen 7800X3D tem 8 cores físicos)
                'seed': -1,                # Seed aleatório
                'num_batch': 256,          # Batch size para throughput
            })

            # Otimizações específicas para Mixtral (se aplicável)
            if 'mixtral' in current_model:
                options['num_gqa'] = 4    # Grouped Query Attention (economiza VRAM)

            response = ollama.chat(
                model=current_model,
                messages=messages_to_send,
                stream=False,
                options=options,
                format=current_format,
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
                        # Tentativa padrão: validação completa
                        parsed_content = response_model.parse_raw(json_str)
                        return parsed_content
                    else:
                        raise json.JSONDecodeError("Conteúdo não contém um JSON válido.", content, 0)
                except (json.JSONDecodeError, pydantic.ValidationError) as e:
                    # Em vez de falhar ruidosamente, construímos um fallback seguro
                    logging.warning("LLMGenerationWarning: resposta do Ollama não corresponde estritamente ao modelo Pydantic; criando objeto de fallback.")
                    logging.debug(f"Validação/JSON erro: {e}")
                    # Tentar extrair o JSON parcial, se houver
                    parsed_dict = None
                    try:
                        parsed_dict = json.loads(json_str)
                    except Exception:
                        try:
                            parsed_dict = json.loads(content)
                        except Exception:
                            parsed_dict = None

                    # Construir valores de fallback para todos os campos do modelo
                    fallback_values = {}
                    model_fields = getattr(response_model, 'model_fields', {}) or getattr(response_model, '__fields__', {})
                    # model_fields em pydantic v2, __fields__ fallback para compatibilidade
                    for fname in model_fields:
                        if isinstance(parsed_dict, dict) and fname in parsed_dict:
                            fallback_values[fname] = parsed_dict[fname]
                        else:
                            # Não temos valor: deixe como None (model_construct evita validação)
                            fallback_values[fname] = None

                    # Construir o objeto sem validação (model_construct - pydantic v2)
                    try:
                        obj = response_model.model_construct(**fallback_values)
                    except Exception:
                        # Último recurso: construir um objeto simples via __init__ com dados disponíveis
                        try:
                            obj = response_model(**{k: v for k, v in (parsed_dict or {}).items() if k in (model_fields or {})})
                        except Exception:
                            # Se tudo falhar, retornar um dicionário com o conteúdo bruto
                            logging.error("LLMGenerationError: Não foi possível construir objeto de fallback do modelo Pydantic.")
                            return {
                                '_validation_error': str(e),
                                '_raw_content': content
                            }

                    # Anexar metadados do erro ao objeto de fallback para diagnóstico
                    try:
                        setattr(obj, '_pydantic_validation_error', str(e))
                        setattr(obj, '_raw_content', content)
                    except Exception:
                        pass

                    return obj
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