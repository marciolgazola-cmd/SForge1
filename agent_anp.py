# agent_anp.py
import logging
import json
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_models import get_agent_model

# Importa os agentes auxiliares para chamar suas funções
from agent_ara import AgentARA, ARAOutput
from agent_aad import AgentAAD, AADSolutionOutput
from agent_agp import AgentAGP, AGPEstimateOutput

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

class AgentANP:
    def __init__(self, llm_simulator: LLMSimulator, ara_agent: AgentARA, aad_agent: AgentAAD, agp_agent: AgentAGP):
        self.llm_simulator = llm_simulator
        self.ara_agent = ara_agent
        self.aad_agent = aad_agent
        self.agp_agent = agp_agent
        self.model_name = get_agent_model('ANP') # Obtém o modelo para ANP
        logger.info(f"AgentANP inicializado com modelo {self.model_name} e pronto para gerar propostas comerciais.")

    def _append_schema_instruction(self, messages: list[Dict[str, str]]):
        schema = ProposalContentOutput.model_json_schema()
        llm_schema_instruction = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }
        schema_str = json.dumps(llm_schema_instruction, indent=2, ensure_ascii=False)
        instruction = (
            "\n\nIMPORTANTE: Responda em JSON preenchendo todos os campos abaixo com informações detalhadas "
            "sobre a proposta. Não deixe valores vazios ou genéricos.\n"
            f"{schema_str}\n"
        )
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += instruction
        else:
            messages.append({"role": "user", "content": instruction})

    def _normalize_str_field(self, value: Any, default: str) -> str:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else default
        if value is None:
            return default
        if isinstance(value, (dict, list)):
            try:
                value = json.dumps(value, ensure_ascii=False, indent=2)
            except Exception:
                value = str(value)
        else:
            value = str(value)
        cleaned = value.strip()
        return cleaned if cleaned else default

    def _normalize_estimated_value(self, raw_value: Any) -> float:
        if isinstance(raw_value, (int, float)):
            return float(raw_value)
        if raw_value is None:
            return 0.0
        cleaned = str(raw_value).replace("R$", "").replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f"AgentANP: Não foi possível converter estimated_value '{raw_value}'. Usando 0.0.")
            return 0.0

    def _normalize_proposal_payload(self, payload: Dict[str, Any], req_data: Dict[str, Any]) -> ProposalContentOutput:
        normalized = {
            "title": self._normalize_str_field(payload.get("title"), f"Proposta para {req_data.get('nome_projeto', 'Projeto sem título')}"),
            "description": self._normalize_str_field(payload.get("description"), "Descrição não fornecida."),
            "problem_understanding_moai": self._normalize_str_field(payload.get("problem_understanding_moai"), "Entendimento não informado."),
            "solution_proposal_moai": self._normalize_str_field(payload.get("solution_proposal_moai"), "Solução não informada."),
            "scope_moai": self._normalize_str_field(payload.get("scope_moai"), "Escopo não definido."),
            "technologies_suggested_moai": self._normalize_str_field(payload.get("technologies_suggested_moai"), "Tecnologias não informadas."),
            "estimated_value_moai": self._normalize_estimated_value(payload.get("estimated_value_moai")),
            "estimated_time_moai": self._normalize_str_field(payload.get("estimated_time_moai"), "Prazo não definido."),
            "terms_conditions_moai": self._normalize_str_field(payload.get("terms_conditions_moai"), "Termos e condições a definir.")
        }
        try:
            return ProposalContentOutput(**normalized)
        except ValidationError as ve:
            logger.error(f"AgentANP: Dados normalizados não correspondem ao esquema: {ve}")
            raise LLMGenerationError(f"Dados normalizados inválidos para proposta: {ve}") from ve

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

            self._append_schema_instruction(messages)

            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                json_mode=True
            )
            raw_content = response_raw.get('content') if isinstance(response_raw, dict) else None
            if not raw_content:
                raise LLMGenerationError("LLM não retornou conteúdo ao gerar a proposta.")

            try:
                payload = json.loads(raw_content)
            except json.JSONDecodeError as jde:
                raise LLMGenerationError(f"LLM não retornou JSON válido para proposta: {jde}") from jde

            proposal_output = self._normalize_proposal_payload(payload, req_data)

            logger.info(f"AgentANP: Proposta comercial gerada com sucesso usando {self.model_name}.")
            return proposal_output.model_dump() # Converte o modelo Pydantic para dicionário

        except (LLMConnectionError, LLMGenerationError, ValueError) as e:
            logger.error(f"AgentANP: Falha ao gerar proposta comercial com o LLM {self.model_name} ou agente auxiliar. Erro: {e}")
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
            logger.error(f"AgentANP: Erro inesperado ao gerar proposta comercial: {e}")
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
        logger.info(f"AgentANP: Versão final da proposta aprovada gerada para {proposal_data.get('title', 'N/A')}.")
        return final_proposal
