# ara_agent.py
import uuid
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelo Pydantic para a resposta do ARA ---
class ARAResponse(BaseModel):
    problem_understanding: str = Field(..., description="Análise detalhada do problema de negócio do cliente.")
    key_requirements: List[str] = Field(..., description="Lista de requisitos chave extraídos.")
    implicit_requirements: List[str] = Field(..., description="Lista de requisitos implícitos ou não explicitados.")
    assumptions: List[str] = Field(..., description="Suposições feitas para a análise.")
    constraints: List[str] = Field(..., description="Restrições identificadas.")
    proposed_next_steps: str = Field(..., description="Próximos passos sugeridos pelo ARA.")

class ARAResponseOld(BaseModel): # Modelo antigo para compatibilidade em caso de falha de parsing do novo.
    problem_understanding: str = Field(..., description="Análise detalhada do problema de negócio do cliente.")

class ARAAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        logging.info("ARAAgent inicializado e pronto para analisar requisitos.")

    def analyze_requirements(self, req_data: Dict[str, Any]) -> str:
        logging.info(f"ARAAgent: Iniciando análise de requisitos para o projeto '{req_data.get('nome_projeto', 'N/A')}'...")

        prompt = f"""
        Com base nos seguintes requisitos do cliente, elabore uma "Análise de Requisitos" detalhada.
        Identifique o problema de negócio, requisitos chave (funcionais e não funcionais),
        requisitos implícitos, suposições e restrições.

        Dados do Cliente:
        Nome do Projeto: {req_data.get('nome_projeto', 'N/A')}
        Nome do Cliente: {req_data.get('nome_cliente', 'N/A')}
        Problema de Negócio: {req_data.get('problema_negocio', 'N/A')}
        Objetivos do Projeto: {req_data.get('objetivos_projeto', 'N/A')}
        Funcionalidades Esperadas: {req_data.get('funcionalidades_esperadas', 'N/A')}
        Restrições: {req_data.get('restricoes', 'N/A')}
        Público-alvo: {req_data.get('publico_alvo', 'N/A')}

        Sua resposta deve ser um JSON estritamente conforme o modelo ARAResponse Pydantic.
        """

        system_message = "Você é o Agente de Análise de Requisitos (ARA) da Synapse Forge. Sua função é traduzir requisitos brutos de clientes em uma análise estruturada e compreensível, identificando claramente problemas, requisitos, suposições e restrições."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            # Chama o método chat do LLMSimulator com o modelo Pydantic
            response_obj = self.llm_simulator.chat(messages, response_model=ARAResponse)
            logging.info(f"ARAAgent: Análise de requisitos concluída para '{req_data.get('nome_projeto', 'N/A')}'.")
            
            # Retorna uma string formatada ou o JSON bruto, dependendo de como o MOAI espera consumir
            # Para manter compatibilidade com o que MOAI espera (uma string markdown), vou formatar aqui.
            formatted_response = f"""
**Análise do Problema de Negócio:**
{response_obj.problem_understanding}

**Requisitos Chave:**
{'- ' + '\n- '.join(response_obj.key_requirements)}

**Requisitos Implícitos:**
{'- ' + '\n- '.join(response_obj.implicit_requirements)}

**Suposições:**
{'- ' + '\n- '.join(response_obj.assumptions)}

**Restrições:**
{'- ' + '\n- '.join(response_obj.constraints)}

**Próximos Passos Sugeridos:**
{response_obj.proposed_next_steps}
"""
            return formatted_response

        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"ARAAgent: Falha ao analisar requisitos para '{req_data.get('nome_projeto', 'N/A')}'. Erro: {e}")
            # Em caso de erro, tenta gerar uma resposta mais simples ou retorna uma mensagem de erro
            error_message = f"Erro ao analisar requisitos com o LLM: {e}. Gerando análise simplificada."
            logging.warning(error_message)
            # Tenta um fallback com uma resposta menos estruturada, se o LLM falhou no Pydantic
            try:
                # Tenta novamente, mas sem o response_model para ver se retorna texto simples
                simple_text_response = self.llm_simulator.chat(messages) 
                if simple_text_response:
                     return f"**Análise Simplificada (Erro LLM Anterior):**\n{simple_text_response}"
                else:
                    return f"**Análise de Requisitos Simplificada (Erro LLM):**\nO LLM não conseguiu gerar uma análise detalhada. {error_message}"
            except Exception as inner_e:
                logging.error(f"ARAAgent: Falha total ao tentar fallback para análise simples: {inner_e}")
                return f"**Análise de Requisitos Indisponível:**\nNão foi possível obter uma análise devido a erros de comunicação com o LLM. {error_message}"
        except Exception as e:
            logging.error(f"ARAAgent: Erro inesperado ao analisar requisitos: {e}")
            return f"**Análise de Requisitos Indisponível (Erro Interno):**\nUm erro inesperado ocorreu: {e}"
