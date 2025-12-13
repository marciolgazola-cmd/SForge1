# agp_agent.py
import uuid
import datetime
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelo Pydantic para a resposta do AGP ---
class AGPResponse(BaseModel):
    estimated_value: Optional[str] = Field(None, description="Valor monetário estimado para o projeto.")
    estimated_time: Optional[str] = Field(None, description="Prazo estimado para a conclusão do projeto.")
    key_milestones: List[str] = Field(default_factory=list, description="Lista dos principais marcos do projeto.")
    resource_estimates: Dict[str, str] = Field(default_factory=dict, description="Estimativa de recursos necessários (e.g., equipe, infraestrutura).")

class AGPAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model = get_agent_model('AGP')  # mistral para estimativas coerentes
        logging.info(f"AGPAgent inicializado com modelo {self.model} e pronto para gerenciar projetos.")

    def estimate_project(self, req_analysis: str, solution_design: Dict[str, str], req_data: Dict[str, Any]) -> Dict[str, str]:
        logging.info(f"AGPAgent: Iniciando estimativa para o projeto '{req_data.get('nome_projeto', 'N/A')}'...")

        prompt = f"""
        Com base na análise de requisitos e no design da solução, forneça uma estimativa detalhada para o projeto.
        Inclua valor monetário estimado, prazo estimado, marcos chave e estimativas de recursos.

        Análise de Requisitos (pelo ARA):
        {req_analysis}

        Design da Solução (pelo AAD):
        Proposta de Solução: {solution_design.get('solution_proposal', 'N/A')}
        Escopo: {solution_design.get('scope', 'N/A')}
        Tecnologias Sugeridas: {solution_design.get('technologies_suggested', 'N/A')}
        Arquitetura: {solution_design.get('architecture_overview', 'N/A')}

        Dados Originais do Cliente:
        Nome do Projeto: {req_data.get('nome_projeto', 'N/A')}
        Nome do Cliente: {req_data.get('nome_cliente', 'N/A')}
        Restrições (relevantes para estimativa): {req_data.get('restricoes', 'N/A')}

        Sua resposta deve ser um JSON estritamente conforme o modelo AGPResponse Pydantic.
        """

        system_message = "Você é o Agente de Gerenciamento de Projetos (AGP) da Synapse Forge. Sua função é fornecer estimativas realistas de tempo, custo e recursos para os projetos, definindo marcos chave e alinhando com as restrições do cliente."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            response_obj = self.llm_simulator.chat(messages, response_model=AGPResponse, model_override=self.model)
            logging.info(f"AGPAgent: Estimativa de projeto concluída para '{req_data.get('nome_projeto', 'N/A')}'.")
            
            # Retorna um dicionário com os campos, como o MOAI espera para preencher a proposta
            return {
                "estimated_value": response_obj.estimated_value,
                "estimated_time": response_obj.estimated_time,
                "key_milestones": response_obj.key_milestones, # MOAI pode usar para timeline
                "resource_estimates": response_obj.resource_estimates # MOAI pode usar para alocação
            }
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"AGPAgent: Falha ao estimar projeto para '{req_data.get('nome_projeto', 'N/A')}'. Erro: {e}")
            error_message = f"Erro ao estimar projeto com o LLM: {e}. Gerando estimativa simplificada."
            logging.warning(error_message)
            try:
                simple_text_response = self.llm_simulator.chat(messages)
                return {
                    "estimated_value": simple_text_response if simple_text_response else f"Valor Estimado Indisponível (Erro LLM): {error_message}",
                    "estimated_time": f"Prazo Estimado Indisponível (Erro LLM): {error_message}",
                    "key_milestones": [],
                    "resource_estimates": {}
                }
            except Exception as inner_e:
                logging.error(f"AGPAgent: Falha total ao tentar fallback para estimativa simples: {inner_e}")
                return {
                    "estimated_value": f"Valor Estimado Indisponível (Erro Interno): {error_message}",
                    "estimated_time": f"Prazo Estimado Indisponível (Erro Interno): {error_message}",
                    "key_milestones": [],
                    "resource_estimates": {}
                }
        except Exception as e:
            logging.error(f"AGPAgent: Erro inesperado ao estimar projeto: {e}")
            return {
                "estimated_value": f"Valor Estimado Indisponível (Erro Interno): {e}",
                "estimated_time": f"Prazo Estimado Indisponível (Erro Interno): {e}",
                "key_milestones": [],
                "resource_estimates": {}
            }
