# aad_agent.py
import uuid
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelo Pydantic para a resposta do AAD ---
class AADResponse(BaseModel):
    solution_proposal: str = Field(..., description="Proposta de solução de alto nível.")
    scope: str = Field(..., description="Escopo detalhado da solução, incluindo funcionalidades e módulos.")
    technologies_suggested: str = Field(..., description="Tecnologias sugeridas para o desenvolvimento da solução.")
    architecture_overview: str = Field(..., description="Visão geral da arquitetura proposta.")
    main_components: List[str] = Field(..., description="Lista dos principais componentes da solução.")

class AADAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        logging.info("AADAgent inicializado e pronto para projetar soluções.")

    def design_solution(self, req_analysis: str, req_data: Dict[str, Any]) -> Dict[str, str]:
        logging.info(f"AADAgent: Iniciando design da solução para o projeto '{req_data.get('nome_projeto', 'N/A')}'...")

        prompt = f"""
        Com base na análise de requisitos fornecida e nos dados originais do cliente,
        proponha uma solução de TI robusta. Detalhe a proposta da solução, o escopo,
        as tecnologias sugeridas, uma visão geral da arquitetura e os principais componentes.

        Análise de Requisitos (pelo ARA):
        {req_analysis}

        Dados Originais do Cliente:
        Nome do Projeto: {req_data.get('nome_projeto', 'N/A')}
        Nome do Cliente: {req_data.get('nome_cliente', 'N/A')}
        Problema de Negócio: {req_data.get('problema_negocio', 'N/A')}
        Objetivos do Projeto: {req_data.get('objetivos_projeto', 'N/A')}
        Funcionalidades Esperadas: {req_data.get('funcionalidades_esperadas', 'N/A')}
        Restrições: {req_data.get('restricoes', 'N/A')}
        Público-alvo: {req_data.get('publico_alvo', 'N/A')}

        Sua resposta deve ser um JSON estritamente conforme o modelo AADResponse Pydantic.
        """

        system_message = "Você é o Agente de Arquitetura e Design (AAD) da Synapse Forge. Sua função é transformar a análise de requisitos em uma proposta de solução técnica detalhada, incluindo arquitetura e tecnologias."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            response_obj = self.llm_simulator.chat(messages, response_model=AADResponse)
            logging.info(f"AADAgent: Design da solução concluído para '{req_data.get('nome_projeto', 'N/A')}'.")
            
            # Retorna um dicionário com os campos, como o MOAI espera para preencher a proposta
            return {
                "solution_proposal": response_obj.solution_proposal,
                "scope": response_obj.scope,
                "technologies_suggested": response_obj.technologies_suggested,
                "architecture_overview": response_obj.architecture_overview,
                "main_components": '\n- '.join(response_obj.main_components) # Convertendo para string para facilitar o display
            }
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"AADAgent: Falha ao projetar a solução para '{req_data.get('nome_projeto', 'N/A')}'. Erro: {e}")
            # Em caso de erro, tenta gerar uma resposta mais simples ou retorna uma mensagem de erro
            error_message = f"Erro ao projetar a solução com o LLM: {e}. Gerando design simplificado."
            logging.warning(error_message)
            try:
                simple_text_response = self.llm_simulator.chat(messages)
                return {
                    "solution_proposal": simple_text_response if simple_text_response else f"Solução Simplificada (Erro LLM): {error_message}",
                    "scope": f"Escopo Simplificado (Erro LLM): {error_message}",
                    "technologies_suggested": f"Tecnologias Simplificadas (Erro LLM): {error_message}",
                    "architecture_overview": f"Arquitetura Simplificada (Erro LLM): {error_message}",
                    "main_components": f"Componentes Simplificados (Erro LLM): {error_message}"
                }
            except Exception as inner_e:
                logging.error(f"AADAgent: Falha total ao tentar fallback para design simples: {inner_e}")
                return {
                    "solution_proposal": f"Solução Indisponível (Erro Interno): {error_message}",
                    "scope": f"Escopo Indisponível (Erro Interno): {error_message}",
                    "technologies_suggested": f"Tecnologias Indisponíveis (Erro Interno): {error_message}",
                    "architecture_overview": f"Arquitetura Indisponível (Erro Interno): {error_message}",
                    "main_components": f"Componentes Indisponíveis (Erro Interno): {error_message}"
                }
        except Exception as e:
            logging.error(f"AADAgent: Erro inesperado ao projetar a solução: {e}")
            return {
                "solution_proposal": f"Solução Indisponível (Erro Interno): {e}",
                "scope": f"Escopo Indisponível (Erro Interno): {e}",
                "technologies_suggested": f"Tecnologias Indisponíveis (Erro Interno): {e}",
                "architecture_overview": f"Arquitetura Indisponível (Erro Interno): {e}",
                "main_components": f"Componentes Indisponíveis (Erro Interno): {e}"
            }
