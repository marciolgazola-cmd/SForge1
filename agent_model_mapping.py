# agent_model_mapping.py
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Mapeamento dos agentes para os modelos LLM que devem utilizar
# Certifique-se de que estes modelos estão disponíveis no seu servidor Ollama
AGENT_MODEL_MAP: Dict[str, str] = {
    'ARA': 'llama3:8b',
    # ALTERAÇÃO AQUI: Use o nome exato do modelo Mixtral que você tem
    'AAD': 'mixtral:8x7b-instruct-v0.1-q4_K_M', # <--- CORRIGIDO
    'AGP': 'llama3:8b',
    # ALTERAÇÃO AQUI: Use o nome exato do modelo Mixtral que você tem
    'ANP': 'mixtral:8x7b-instruct-v0.1-q4_K_M', # <--- CORRIGIDO
    'ADE-X': 'codellama:13b',
    'AQT': 'llama3:8b',
    # ALTERAÇÃO AQUI: Use o nome exato do modelo Mixtral que você tem
    'ASE': 'mixtral:8x7b-instruct-v0.1-q4_K_M', # <--- CORRIGIDO
    'ADO': 'llama3:8b',
    'AMS': 'llama3:8b',
    'AID': 'codellama:13b',
    'MOAI_Chat': 'llama3:8b',
}

def get_agent_model(agent_code: str) -> str:
    """
    Retorna o nome do modelo LLM associado a um agente específico.
    Se o agente não estiver mapeado, retorna um modelo padrão e loga um aviso.
    """
    model = AGENT_MODEL_MAP.get(agent_code)
    if not model:
        fallback_model = 'llama3:8b'
        logger.warning(f"Modelo LLM não especificado para o agente '{agent_code}'. Usando o modelo padrão: '{fallback_model}'.")
        return fallback_model
    return model

