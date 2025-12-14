# anp_agent.py
import logging
import json
from typing import Dict, Any, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model

# Importa os agentes auxiliares para chamar suas funções
from ara_agent import ARAAgent, ARAOutput
from aad_agent import AADAgent, AADSolutionOutput
from agp_agent import AGPAgent, AGPEstimateOutput

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para a proposta gerada pelo ANP
class ProposalContentOutput(BaseModel):
    title: str = Field(description="Título da proposta comercial.")
    description: str = Field(description="Descrição geral da proposta.")
    problem_understanding_moai: str = Field(description="Entendimento do problema de negócio pelo MOAI.")
    solution_proposal_moai: str = Field(description="Proposta de solução detalhada pelo MOAI.")
    scope_moai: str = Field(description="Escopo do projeto.")
    technologies_suggested_moai: str = Field(description="Tecnologias sugeridas.")
    estimated_value_moai: float = Field(description="Valor estimado da proposta.")
    estimated_time_moai: str = Field(description="Prazo estimado de entrega.")
    terms_conditions_moai: str = Field(description="Termos e condições gerais.")

class ANPAgent:
    def __init__(self, llm_simulator: LLMSimulator, ara_agent: ARAAgent, aad_agent: AADAgent, agp_agent: AGPAgent):
        self.llm_simulator = llm_simulator
        self.ara_agent = ara_agent
        self.aad_agent = aad_agent
        self.agp_agent = agp_agent
        self.model_name = get_agent_model('ANP') # Obtém o modelo para ANP
        logger.info(f"ANPAgent inicializado com modelo {self.model_name} e pronto para gerar propostas comerciais.")

    def generate_proposal_content(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orquestra ARA, AAD e AGP para compilar uma proposta comercial.
        """
        try:
            # 1. ARA refina os requisitos
            refined_requirements = self.ara_agent.analyze_requirements(req_data)
            if refined_requirements.get("error"):
                raise ValueError(f"Erro na análise de requisitos pelo ARA: {refined_requirements['error']}")

            # 2. AAD projeta a solução
            solution_design = self.aad_agent.design_solution(req_data.get('nome_projeto', 'Novo Projeto'), refined_requirements)
            if solution_design.get("error"):
                raise ValueError(f"Erro no design da solução pelo AAD: {solution_design['error']}")

            # 3. AGP estima o projeto
            project_estimate = self.agp_agent.estimate_project(req_data.get('nome_projeto', 'Novo Projeto'), refined_requirements, solution_design)
            if project_estimate.get("error"):
                raise ValueError(f"Erro na estimativa do projeto pelo AGP: {project_estimate['error']}")

            prompt = f"""
            Compile uma proposta comercial detalhada e persuasiva com base nas informações a seguir.
            Apresente o problema, a solução proposta, o escopo, as tecnologias, o valor e o prazo estimados, e termos e condições gerais.

            Requisitos Brutos:
            {json.dumps(req_data, indent=2, ensure_ascii=False)}

            Requisitos Refinados (ARA):
            {json.dumps(refined_requirements, indent=2, ensure_ascii=False)}

            Design da Solução (AAD):
            {json.dumps(solution_design, indent=2, ensure_ascii=False)}

            Estimativa de Projeto (AGP):
            {json.dumps(project_estimate, indent=2, ensure_ascii=False)}

            Sua resposta DEVE ser um objeto JSON.
            """

            messages = [
                {"role": "system", "content": "Você é o Agente de Negócios e Propostas (ANP). Sua tarefa é gerar propostas comerciais completas e convincentes, integrando informações de outros agentes."
                                                    "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para ProposalContentOutput."},
                {"role": "user", "content": prompt}
            ]

            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=ProposalContentOutput,
                json_mode=True
            )
            response: ProposalContentOutput = cast(ProposalContentOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"ANPAgent: Proposta comercial gerada com sucesso usando {self.model_name}.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário

        except (LLMConnectionError, LLMGenerationError, ValueError) as e:
            logger.error(f"ANPAgent: Falha ao gerar proposta comercial com o LLM {self.model_name} ou agente auxiliar. Erro: {e}")
            # Retorna um dicionário com informações de erro e campos padrão para que o MOAI possa processar
            return {
                "error": str(e),
                "message": f"Falha ao gerar proposta comercial: {e}.",
                "title": f"Proposta (Erro) - {req_data.get('nome_projeto', 'N/A')}",
                "description": "Houve um erro na geração da proposta. Por favor, revise manualmente.",
                "problem_understanding_moai": "",
                "solution_proposal_moai": "",
                "scope_moai": "",
                "technologies_suggested_moai": "",
                "estimated_value_moai": 0.0,
                "estimated_time_moai": "Indefinido",
                "terms_conditions_moai": ""
            }
        except Exception as e:
            logger.error(f"ANPAgent: Erro inesperado ao gerar proposta comercial: {e}")
            return {
                "error": str(e),
                "message": f"Erro inesperado ao gerar proposta comercial: {e}.",
                "title": f"Proposta (Erro Inesperado) - {req_data.get('nome_projeto', 'N/A')}",
                "description": "Houve um erro inesperado na geração da proposta. Por favor, revise manualmente.",
                "problem_understanding_moai": "",
                "solution_proposal_moai": "",
                "scope_moai": "",
                "technologies_suggested_moai": "",
                "estimated_value_moai": 0.0,
                "estimated_time_moai": "Indefinido",
                "terms_conditions_moai": ""
            }

    def generate_approved_proposal_content(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera uma versão final de uma proposta aprovada, que pode incluir mais detalhes ou formatação.
        """
        # Para este exemplo, vamos simplificar e apenas adicionar um status de "Finalizado"
        # Em um cenário real, o LLM poderia reformatar ou enriquecer a proposta.
        final_proposal = proposal_data.copy()
        final_proposal['description'] += "\n\nEsta é a versão final da proposta aprovada, pronta para execução."
        logger.info(f"ANPAgent: Versão final da proposta aprovada gerada para {proposal_data.get('title', 'N/A')}.")
        return final_proposal
