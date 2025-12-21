# agent_ara.py
import logging
import json # Adicionado
from typing import Dict, Any, List, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_models import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o ARA, se ele usar response_model
class ARAOutput(BaseModel):
    summary: str = Field(description="Um resumo conciso dos requisitos do cliente.")
    key_features: List[str] = Field(description="Lista das principais funcionalidades identificadas.")
    risks: List[str] = Field(description="Potenciais riscos e desafios.")
    estimated_effort: str = Field(description="Estimativa de esforço ou complexidade inicial.")

class AgentARA:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('ARA') # Obtém o modelo para ARA
        logger.info(f"AgentARA inicializado com modelo {self.model_name} e pronto para analisar requisitos.")

    def analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa os requisitos brutos do cliente e os refina.
        """
        prompt = f"""
        Analise os seguintes requisitos do cliente e forneça um resumo conciso,
        identifique as principais funcionalidades esperadas, liste potenciais riscos
        e estime o esforço inicial.

        Requisitos do Cliente:
        {json.dumps(requirements, indent=2, ensure_ascii=False)}

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Análise de Requisitos (ARA). Sua tarefa é refinar e estruturar os requisitos do cliente de forma clara e objetiva."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para ARAOutput."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=ARAOutput,
                json_mode=True
            )
            response: ARAOutput = cast(ARAOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"AgentARA: Requisitos analisados com sucesso usando {self.model_name}.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AgentARA: Falha ao analisar requisitos com o LLM {self.model_name}. Erro: {e}")
            return {"error": str(e), "message": f"Falha na análise de requisitos: {e}", "summary": "(Erro na análise)"}
        except Exception as e:
            logger.error(f"AgentARA: Erro inesperado ao analisar requisitos: {e}")
            return {"error": str(e), "message": f"Erro inesperado na análise de requisitos: {e}", "summary": "(Erro inesperado)"}
