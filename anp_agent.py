# anp_agent.py
import uuid
import datetime
from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field, field_validator
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from ara_agent import ARAAgent
from aad_agent import AADAgent
from agp_agent import AGPAgent
from agent_model_mapping import get_agent_model
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelo Pydantic para a proposta comercial final ---
class ANPProposalContent(BaseModel):
    title: Optional[str] = Field(None, description="Título da proposta comercial.")
    description: Optional[str] = Field(None, description="Breve descrição da proposta.")
    problem_understanding_moai: Optional[str] = Field(None, description="Análise do problema (do ARA).")
    solution_proposal_moai: Optional[str] = Field(None, description="Proposta de solução (do AAD).")
    scope_moai: Optional[str] = Field(None, description="Escopo detalhado (do AAD).")
    technologies_suggested_moai: Optional[Union[str, List[str]]] = Field(None, description="Tecnologias sugeridas (do AAD).")
    estimated_value_moai: Optional[str] = Field(None, description="Valor estimado (do AGP).")
    estimated_time_moai: Optional[str] = Field(None, description="Prazo estimado (do AGP).")
    terms_conditions_moai: Optional[str] = Field(None, description="Termos e condições gerais da proposta.")
    
    @field_validator('technologies_suggested_moai', mode='before')
    @classmethod
    def convert_tech_list_to_string(cls, v):
        """Converte listas de tecnologias em string formatada"""
        if v is None:
            return None
        if isinstance(v, list):
            return ", ".join([str(tech) for tech in v])
        return str(v) if v else None

class ANPAgent:
    def __init__(self, llm_simulator: LLMSimulator, ara_agent: ARAAgent, aad_agent: AADAgent, agp_agent: AGPAgent):
        self.llm_simulator = llm_simulator
        self.ara_agent = ara_agent
        self.aad_agent = aad_agent
        self.agp_agent = agp_agent
        self.model = get_agent_model('ANP')  # mistral para propostas persuasivas
        logging.info(f"ANPAgent inicializado com modelo {self.model} e pronto para gerar propostas comerciais.")

    def generate_proposal_content(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"ANPAgent: Gerando conteúdo da proposta para o projeto '{req_data.get('nome_projeto', 'N/A')}'...")
        
        # 1. Aciona ARA para análise de requisitos
        problem_understanding = self.ara_agent.analyze_requirements(req_data)

        # 2. Aciona AAD para design da solução
        solution_design = self.aad_agent.design_solution(problem_understanding, req_data) # Retorna Dict

        # 3. Aciona AGP para estimativa
        project_estimates = self.agp_agent.estimate_project(problem_understanding, solution_design, req_data) # Retorna Dict

        # Consolida as informações e gera a proposta comercial final
        prompt = f"""
        Com base nas análises e designs fornecidos pelos agentes internos e nos requisitos originais do cliente,
        crie uma proposta comercial de TI persuasiva e detalhada.
        A proposta deve incluir: título, descrição breve, análise do problema, proposta de solução,
        escopo, tecnologias sugeridas, valor estimado, prazo estimado e termos/condições gerais.

        Dados Originais do Cliente:
        Nome do Projeto: {req_data.get('nome_projeto', 'N/A')}
        Nome do Cliente: {req_data.get('nome_cliente', 'N/A')}
        Problema de Negócio: {req_data.get('problema_negocio', 'N/A')}
        Objetivos do Projeto: {req_data.get('objetivos_projeto', 'N/A')}
        Funcionalidades Esperadas: {req_data.get('funcionalidades_esperadas', 'N/A')}
        Restrições: {req_data.get('restricoes', 'N/A')}
        Público-alvo: {req_data.get('publico_alvo', 'N/A')}

        Análise do Problema (ARA):
        {problem_understanding}

        Design da Solução (AAD):
        Proposta de Solução: {solution_design.get('solution_proposal', 'N/A')}
        Escopo: {solution_design.get('scope', 'N/A')}
        Tecnologias Sugeridas: {solution_design.get('technologies_suggested', 'N/A')}
        Visão Geral da Arquitetura: {solution_design.get('architecture_overview', 'N/A')}
        Componentes Principais: {solution_design.get('main_components', 'N/A')}

        Estimativas (AGP):
        Valor Estimado: {project_estimates.get('estimated_value', 'N/A')}
        Prazo Estimado: {project_estimates.get('estimated_time', 'N/A')}
        Marcos Chave: {project_estimates.get('key_milestones', [])}
        Estimativa de Recursos: {project_estimates.get('resource_estimates', {})}

        Sua resposta deve ser um JSON estritamente conforme o modelo ANPProposalContent Pydantic.
        """

        system_message = "Você é o Agente de Negócios e Propostas (ANP) da Synapse Forge. Sua função é consolidar as informações dos outros agentes (ARA, AAD, AGP) e criar propostas comerciais persuasivas e completas para os clientes. Priorize clareza, profissionalismo e alinhamento com as necessidades do cliente."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            # Chama o método chat do LLMSimulator com o modelo Pydantic para a proposta final
            proposal_content_obj = self.llm_simulator.chat(messages, response_model=ANPProposalContent, model_override=self.model)
            logging.info(f"ANPAgent: Conteúdo da proposta comercial gerado para '{req_data.get('nome_projeto', 'N/A')}'.")

            # Converte para dict e garante que valores None virem como strings vazias
            proposal_dict = proposal_content_obj.dict()
            return {
                "title": proposal_dict.get('title') or "",
                "description": proposal_dict.get('description') or "",
                "problem_understanding_moai": proposal_dict.get('problem_understanding_moai') or "",
                "solution_proposal_moai": proposal_dict.get('solution_proposal_moai') or "",
                "scope_moai": proposal_dict.get('scope_moai') or "",
                "technologies_suggested_moai": proposal_dict.get('technologies_suggested_moai') or "",
                "estimated_value_moai": proposal_dict.get('estimated_value_moai') or None,
                "estimated_time_moai": proposal_dict.get('estimated_time_moai') or "",
                "terms_conditions_moai": proposal_dict.get('terms_conditions_moai') or ""
            }
        
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"ANPAgent: Falha ao gerar conteúdo da proposta para '{req_data.get('nome_projeto', 'N/A')}'. Erro: {e}")
            error_message = f"Erro ao gerar proposta comercial com o LLM: {e}. Gerando proposta com dados padrão."
            logging.warning(error_message)
            # Fallback para dados padrão em caso de erro grave do LLM
            return {
                "title": f"Proposta para {req_data.get('nome_projeto', 'Novo Projeto')} (Rascunho - Erro LLM)",
                "description": f"Proposta inicial gerada automaticamente. Necessita de revisão manual devido a um erro na geração do conteúdo pelo LLM. {error_message}",
                "problem_understanding_moai": problem_understanding, # Mantém o que conseguiu dos outros agentes
                "solution_proposal_moai": solution_design.get('solution_proposal', 'Solução padrão devido a erro do LLM'),
                "scope_moai": solution_design.get('scope', 'Escopo padrão devido a erro do LLM'),
                "technologies_suggested_moai": solution_design.get('technologies_suggested', 'Tecnologias padrão devido a erro do LLM'),
                "estimated_value_moai": project_estimates.get('estimated_value', 'R$ 0,00 (Erro LLM)'),
                "estimated_time_moai": project_estimates.get('estimated_time', 'Prazo Indefinido (Erro LLM)'),
                "terms_conditions_moai": f"Termos e Condições Padrão. {error_message}"
            }
        except Exception as e:
            logging.error(f"ANPAgent: Erro inesperado ao gerar proposta comercial: {e}")
            return {
                "title": f"Proposta para {req_data.get('nome_projeto', 'Novo Projeto')} (Rascunho - Erro Interno)",
                "description": f"Proposta inicial gerada automaticamente. Necessita de revisão manual devido a um erro inesperado: {e}",
                "problem_understanding_moai": problem_understanding, # Mantém o que conseguiu dos outros agentes
                "solution_proposal_moai": solution_design.get('solution_proposal', 'Solução padrão devido a erro interno'),
                "scope_moai": solution_design.get('scope', 'Escopo padrão devido a erro interno'),
                "technologies_suggested_moai": solution_design.get('technologies_suggested', 'Tecnologias padrão devido a erro interno'),
                "estimated_value_moai": project_estimates.get('estimated_value', 'R$ 0,00 (Erro Interno)'),
                "estimated_time_moai": project_estimates.get('estimated_time', 'Prazo Indefinido (Erro Interno)'),
                "terms_conditions_moai": f"Termos e Condições Padrão. Erro: {e}"
            }

    def generate_approved_proposal_content(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"ANPAgent: Gerando proposta aprovada (reformulada, se necessário) para o projeto '{proposal_data.get('title', 'N/A')}'...")

        # Este método poderia ser usado para refinar a proposta após aprovação
        # para incluir detalhes finais ou ajustar linguagem. Por simplicidade,
        # vamos reutilizar o conteúdo existente por enquanto, mas com a estrutura
        # que permite um LLM mais tarde.

        prompt = f"""
        A seguinte proposta foi aprovada. Revise o conteúdo para garantir que ele esteja pronto para apresentação final,
        removendo quaisquer marcadores de rascunho e adicionando uma breve introdução ou conclusão que celebre a aprovação.
        Mantenha a estrutura e o conteúdo principal.

        Proposta Original Aprovada:
        Título: {proposal_data.get('title', 'N/A')}
        Descrição: {proposal_data.get('description', 'N/A')}
        Análise do Problema: {proposal_data.get('problem_understanding_moai', 'N/A')}
        Solução Proposta: {proposal_data.get('solution_proposal_moai', 'N/A')}
        Escopo: {proposal_data.get('scope_moai', 'N/A')}
        Tecnologias Sugeridas: {proposal_data.get('technologies_suggested_moai', 'N/A')}
        Valor Estimado: {proposal_data.get('estimated_value_moai', 'N/A')}
        Prazo Estimado: {proposal_data.get('estimated_time_moai', 'N/A')}
        Termos e Condições: {proposal_data.get('terms_conditions_moai', 'N/A')}

        Sua resposta deve ser um JSON estritamente conforme o modelo ANPProposalContent Pydantic.
        """

        system_message = "Você é o Agente de Negócios e Propostas (ANP) da Synapse Forge. Após a aprovação de uma proposta, sua função é refiná-la para a versão final de apresentação ao cliente, garantindo profissionalismo e clareza."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            # Chama o método chat do LLMSimulator com o modelo Pydantic para a proposta final
            proposal_content_obj = self.llm_simulator.chat(messages, response_model=ANPProposalContent)
            logging.info(f"ANPAgent: Conteúdo da proposta aprovada gerado para '{proposal_data.get('title', 'N/A')}'.")
            return proposal_content_obj.dict()
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"ANPAgent: Falha ao gerar conteúdo da proposta aprovada para '{proposal_data.get('title', 'N/A')}'. Erro: {e}")
            error_message = f"Erro ao gerar proposta aprovada com o LLM: {e}. Reutilizando dados existentes."
            logging.warning(error_message)
            # Fallback para dados padrão ou existentes em caso de erro
            return {
                "title": f"{proposal_data.get('title', 'Proposta Aprovada')} (Final - Erro LLM)",
                "description": f"Versão final da proposta. Algumas seções podem ser a versão original devido a erro na reformulação pelo LLM. {error_message}",
                "problem_understanding_moai": proposal_data.get('problem_understanding_moai', 'N/A'),
                "solution_proposal_moai": proposal_data.get('solution_proposal_moai', 'N/A'),
                "scope_moai": proposal_data.get('scope_moai', 'N/A'),
                "technologies_suggested_moai": proposal_data.get('technologies_suggested_moai', 'N/A'),
                "estimated_value_moai": proposal_data.get('estimated_value_moai', 'N/A'),
                "estimated_time_moai": proposal_data.get('estimated_time_moai', 'N/A'),
                "terms_conditions_moai": proposal_data.get('terms_conditions_moai', 'N/A') + f"\n\n({error_message})"
            }
        except Exception as e:
            logging.error(f"ANPAgent: Erro inesperado ao gerar proposta aprovada: {e}")
            return {
                "title": f"{proposal_data.get('title', 'Proposta Aprovada')} (Final - Erro Interno)",
                "description": f"Versão final da proposta. Algumas seções podem ser a versão original devido a erro inesperado: {e}",
                "problem_understanding_moai": proposal_data.get('problem_understanding_moai', 'N/A'),
                "solution_proposal_moai": proposal_data.get('solution_proposal_moai', 'N/A'),
                "scope_moai": proposal_data.get('scope_moai', 'N/A'),
                "technologies_suggested_moai": proposal_data.get('technologies_suggested_moai', 'N/A'),
                "estimated_value_moai": proposal_data.get('estimated_value_moai', 'N/A'),
                "estimated_time_moai": proposal_data.get('estimated_time_moai', 'N/A'),
                "terms_conditions_moai": proposal_data.get('terms_conditions_moai', 'N/A') + f"\n\n(Erro Interno: {e})"
            }
