# agp_agent.py
import logging
import json # Adicionado
from typing import Dict, Any, List, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o AGP
class AGPEstimateOutput(BaseModel):
    estimated_time: str = Field(description="Estimativa de tempo para o projeto (ex: '4 meses', '2 semanas').")
    estimated_cost: float = Field(description="Custo estimado em moeda (ex: 50000.00).")
    milestones: List[Dict[str, str]] = Field(description="Principais marcos do projeto com prazos estimados.")
    resource_needs: List[str] = Field(description="Recursos humanos ou técnicos necessários.")

class AGPAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('AGP') # Obtém o modelo para AGP
        logger.info(f"AGPAgent inicializado com modelo {self.model_name} e pronto para gerenciar projetos.")

    def estimate_project(self, project_name: str, requirements: Dict[str, Any], solution_design: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estima o tempo, custo e recursos necessários para o projeto.
        """
        prompt = f"""
        Estime o tempo, custo e recursos necessários para o projeto '{project_name}'.
        Considere os seguintes requisitos e design da solução:

        Requisitos:
        {json.dumps(requirements, indent=2, ensure_ascii=False)}

        Design da Solução:
        {json.dumps(solution_design, indent=2, ensure_ascii=False)}

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Gerenciamento de Projetos (AGP). Sua tarefa é fornecer estimativas realistas de tempo, custo e recursos."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para AGPEstimateOutput."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=AGPEstimateOutput,
                json_mode=True
            )
            response: AGPEstimateOutput = cast(AGPEstimateOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"AGPAgent: Estimativa de projeto gerada com sucesso usando {self.model_name}.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AGPAgent: Falha ao estimar projeto com o LLM {self.model_name}. Erro: {e}")
            return {"error": str(e), "message": f"Falha na estimativa de projeto: {e}", "estimated_time": "(Erro)", "estimated_cost": 0.0}
        except Exception as e:
            logger.error(f"AGPAgent: Erro inesperado ao estimar projeto: {e}")
            return {"error": str(e), "message": f"Erro inesperado na estimativa de projeto: {e}", "estimated_time": "(Erro inesperado)", "estimated_cost": 0.0}
