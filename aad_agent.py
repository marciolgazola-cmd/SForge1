# aad_agent.py
import logging
import json # Adicionado
from typing import Dict, Any, List, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o AAD
class AADSolutionOutput(BaseModel):
    architecture_overview: str = Field(description="Visão geral da arquitetura proposta.")
    tech_stack: List[str] = Field(description="Tecnologias recomendadas (linguagens, frameworks, bancos de dados)." )
    modules: List[Dict[str, str]] = Field(description="Lista de módulos principais com suas responsabilidades.")
    diagram_description: str = Field(description="Descrição para gerar um diagrama de arquitetura.")

class AADAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('AAD') # Obtém o modelo para AAD
        logger.info(f"AADAgent inicializado com modelo {self.model_name} e pronto para projetar soluções.")

    def design_solution(self, project_name: str, refined_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma proposta de arquitetura e design com base nos requisitos refinados.
        """
        prompt = f"""
        Com base nos requisitos refinados para o projeto '{project_name}', crie uma proposta de arquitetura e design.
        Inclua uma visão geral da arquitetura, a pilha tecnológica recomendada, módulos principais com suas responsabilidades
        e uma descrição para gerar um diagrama de arquitetura.

        Requisitos Refinados:
        {json.dumps(refined_requirements, indent=2, ensure_ascii=False)}

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Arquitetura e Design (AAD). Sua tarefa é traduzir requisitos em um design de solução técnico e claro."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para AADSolutionOutput."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=AADSolutionOutput,
                json_mode=True
            )
            response: AADSolutionOutput = cast(AADSolutionOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"AADAgent: Solução projetada com sucesso usando {self.model_name}.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AADAgent: Falha ao projetar solução com o LLM {self.model_name}. Erro: {e}")
            return {"error": str(e), "message": f"Falha no design da solução: {e}", "architecture_overview": "(Erro no design)"}
        except Exception as e:
            logger.error(f"AADAgent: Erro inesperado ao projetar solução: {e}")
            return {"error": str(e), "message": f"Erro inesperado no design da solução: {e}", "architecture_overview": "(Erro inesperado)"}
