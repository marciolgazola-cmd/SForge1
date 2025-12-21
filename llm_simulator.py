# llm_simulator.py
import concurrent.futures
import json
import logging
import os
import time
from typing import List, Dict, Any, Optional, Union

import ollama
from pydantic import BaseModel, ValidationError

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define custom exceptions
class LLMConnectionError(Exception):
    """Custom exception for LLM connection issues."""
    pass

class LLMGenerationError(Exception):
    """Custom exception for LLM generation errors (e.g., malformed response)."""
    pass

class LLMSimulator:
    """
    Simula e gerencia a conexão com um servidor Ollama para interações com LLMs.
    Encapsula a lógica de conexão, verificação de disponibilidade e chamada dos modelos.
    """
    def __init__(self, host: str = 'http://localhost:11434', eager_init: bool = False):
        self.host = host
        self.client: Optional[ollama.Client] = None
        self._is_available = False # Internal flag for connection status
        self._last_check_at = 0.0
        self._check_timeout_seconds = float(os.getenv("OLLAMA_CHECK_TIMEOUT", "2"))
        self._chat_check_timeout_seconds = float(os.getenv("OLLAMA_CHAT_CHECK_TIMEOUT", "10"))
        self._check_cooldown_seconds = float(os.getenv("OLLAMA_CHECK_COOLDOWN", "5"))

        if eager_init:
            self._initialize_client(timeout=self._check_timeout_seconds)

    def _run_with_timeout(self, fn, timeout_seconds: Optional[float]):
        if not timeout_seconds or timeout_seconds <= 0:
            return fn()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn)
            return future.result(timeout=timeout_seconds)

    def _initialize_client(self, timeout: Optional[float] = None) -> bool:
        """Tenta inicializar o cliente Ollama e verificar a conexão."""
        try:
            def _connect_and_list():
                temp_client = ollama.Client(host=self.host)
                temp_client.list()
                return temp_client

            temp_client = self._run_with_timeout(_connect_and_list, timeout)
            self.client = temp_client
            self._is_available = True
            logger.info(f"LLMSimulator: Conectado com sucesso ao Ollama em {self.host}")
            return True
        except concurrent.futures.TimeoutError:
            self.client = None
            self._is_available = False
            logger.warning("LLMSimulator: Timeout ao conectar no Ollama.")
            return False
        except Exception as e:
            # If any part of the initialization/connection test fails, ensure client is None
            # and status is unavailable.
            self.client = None 
            self._is_available = False
            logger.error(f"LLMSimulator: Falha ao conectar ao Ollama em {self.host}. Erro: {e}")
            return False

    def is_available(self, timeout: Optional[float] = None) -> bool:
        """
        Verifica se o cliente LLM está atualmente disponível e funcional.
        Realiza uma verificação dinâmica para confirmar a conexão ativa.
        """
        now = time.time()
        if now - self._last_check_at < self._check_cooldown_seconds:
            return self._is_available
        self._last_check_at = now

        if self.client is None:
            return self._initialize_client(timeout=timeout or self._check_timeout_seconds)

        if self.client is None:
            # If the client was never successfully initialized or explicitly set to None,
            # it's not available.
            self._is_available = False # Ensure internal state is consistent
            return False
        
        try:
            # Attempt a lightweight operation to confirm the connection is active.
            # This handles cases where the Ollama server might have gone down after
            # initial successful connection.
            self._run_with_timeout(self.client.list, timeout or self._check_timeout_seconds)
            self._is_available = True # Confirm the internal state is consistent
            return True
        except concurrent.futures.TimeoutError:
            logger.warning("LLMSimulator: Timeout ao verificar Ollama.")
            self.client = None
            self._is_available = False
            return False
        except Exception as e:
            # If the dynamic check fails, log it and update the status.
            logger.warning(f"LLMSimulator: Cliente Ollama ficou indisponível ou conexão falhou durante verificação dinâmica: {e}")
            self.client = None # Explicitly set client to None as it's no longer functional
            self._is_available = False
            return False

    def chat(self, messages: List[Dict[str, str]], model: str = "mistral", response_model: Optional[type[BaseModel]] = None, json_mode: bool = False) -> Union[Dict[str, Any], BaseModel]:
        """
        Simula uma interação de chat com o LLM.
        Se response_model é fornecido, tenta analisar a resposta para esse modelo Pydantic.
        Se json_mode é True, solicita saída JSON ao LLM.
        """
        # First, check availability. This will raise LLMConnectionError if not available.
        if not self.is_available(timeout=self._chat_check_timeout_seconds):
            raise LLMConnectionError("LLM não está disponível. O servidor Ollama pode estar inativo ou mal configurado.")

        # CRÍTICO: Segunda verificação explícita. Após is_available() retornar True, self.client DEVE ser um objeto.
        # Se por algum motivo extremamente raro e inesperado self.client for None aqui, isto irá capturar.
        if self.client is None:
            logger.critical("LLMSimulator: Inconsistência crítica detectada - self.client é None imediatamente antes da chamada chat(), mesmo após is_available() retornar True. Isso não deveria acontecer.")
            raise LLMConnectionError("Erro interno grave: O cliente Ollama não está disponível apesar das verificações de estado.")
        
        # If response_model is provided, json_mode should implicitly be True for best results.
        if response_model and not json_mode:
            logger.warning("LLMSimulator: 'response_model' foi fornecido, mas 'json_mode' não era True. Para melhores resultados com modelos Pydantic, defina json_mode=True.")
            json_mode = True # Força o modo JSON se um response_model é esperado

        try:
            # Create a mutable copy of messages to append instructions if needed.
            ollama_messages = list(messages) 
            
            if response_model:
                # Get the Pydantic model's JSON schema
                full_schema_dict = response_model.model_json_schema()
                
                # We want the LLM to output an object that *conforms* to the structure described in 'properties'
                # and respects 'required' fields, but NOT to output the 'properties' key itself.
                llm_schema_instruction = {
                    "type": "object",
                    "properties": full_schema_dict.get('properties', {}),
                }
                if 'required' in full_schema_dict:
                    llm_schema_instruction['required'] = full_schema_dict['required']

                schema_str_for_llm = json.dumps(llm_schema_instruction, indent=2)
                
                # Clarified instruction: generate the object, not its schema wrapper.
                instruction = (
                    f"\n\nSua resposta DEVE ser um objeto JSON estritamente conforme o seguinte ESQUEMA. "
                    f"Não o encapsule em uma chave 'properties' ou 'type' de nível superior na sua resposta. "
                    f"APENAS gere o objeto JSON em si, sem texto explicativo antes ou depois:\n"
                    f"```json\n{schema_str_for_llm}\n```"
                )
                
                # Append instruction to the last user message, or add a new one
                if ollama_messages and ollama_messages[-1]['role'] == 'user':
                    ollama_messages[-1]['content'] += instruction
                else:
                    ollama_messages.append({'role': 'user', 'content': instruction})

                logger.debug(f"LLMSimulator: Enviando mensagens com instrução de esquema Pydantic para o modelo {model}")

            # Call the Ollama chat API.
            response = self.client.chat(
                model=model,
                messages=ollama_messages,
                options={'temperature': 0.7}, # Example option, can be customized or passed dynamically
                format='json' if json_mode else '' # Ollama's 'format' parameter for JSON output
            )
            
            # Extract the raw content from the LLM's response.
            raw_content = response['message']['content']
            
            if response_model:
                try:
                    # First, try to validate directly against the response_model
                    parsed_response = response_model.model_validate_json(raw_content)
                    return parsed_response
                except ValidationError as ve:
                    # If direct validation fails, check if the LLM wrapped it in 'properties'
                    try:
                        # Attempt to load the raw content as a dictionary
                        temp_dict = json.loads(raw_content)
                        # Check if it's a dict and contains a 'properties' key whose value is also a dict
                        if isinstance(temp_dict, dict) and 'properties' in temp_dict and isinstance(temp_dict['properties'], dict):
                            logger.warning(f"LLM for {response_model.__name__} generated JSON wrapped in 'properties'. Attempting to extract and validate inner content.")
                            # Validate the content *inside* the 'properties' key
                            parsed_response = response_model.model_validate(temp_dict['properties'])
                            return parsed_response
                        # If not wrapped in 'properties' or not a dict, re-raise the original validation error
                        raise ve
                    except (json.JSONDecodeError, ValidationError) as inner_e:
                        # If parsing the wrapper fails, or inner validation fails,
                        # log both errors and re-raise the original validation error.
                        logger.error(f"LLMGenerationError: Falha ao lidar com o wrapper 'properties' para {response_model.__name__}. Erro de validação original: {ve}. Erro interno de parsing/validação: {inner_e}. Conteúdo bruto: {raw_content[:500]}...")
                        raise ve # Re-raise the original ValidationError for consistency
                except json.JSONDecodeError as jde:
                    logger.error(f"LLMGenerationError: Falha ao decodificar JSON da resposta do LLM para {response_model.__name__}. Erro: {jde}. Conteúdo bruto: {raw_content[:500]}...")
                    raise LLMGenerationError(f"LLM não retornou JSON válido para {response_model.__name__}. Erro de Decodificação JSON: {jde}")
            
            # If no response_model is specified, return the content as a dictionary.
            return {'content': raw_content}

        except LLMConnectionError:
            # Re-raise explicit connection errors for upstream handling.
            raise
        except ollama.ResponseError as re:
            # Catch Ollama API specific errors.
            logger.error(f"LLMGenerationError: Erro da API Ollama: {re}. Modelo: {model}")
            raise LLMGenerationError(f"Erro da API Ollama durante a geração: {re}")
        except Exception as e:
            # Catch any other unexpected errors during the chat interaction.
            logger.error(f"LLMGenerationError: Ocorreu um erro inesperado durante o chat do LLM: {e}", exc_info=True)
            raise LLMGenerationError(f"Erro inesperado durante a interação com o LLM: {e}")
