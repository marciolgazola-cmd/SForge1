# agp_agent.py
import logging
import json # Adicionado
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ValidationError
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

    def _append_schema_instruction(self, messages: list[Dict[str, str]]):
        schema = AGPEstimateOutput.model_json_schema()
        llm_schema_instruction = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }
        schema_str = json.dumps(llm_schema_instruction, indent=2, ensure_ascii=False)
        instruction = (
            "\n\nIMPORTANTE: Responda com um JSON completo seguindo o esquema abaixo, preenchendo cada campo "
            "com estimativas realistas e detalhadas.\n"
            f"{schema_str}\n"
        )
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += instruction
        else:
            messages.append({"role": "user", "content": instruction})

    def _normalize_milestones(self, raw_milestones: Any) -> List[Dict[str, str]]:
        """
        Garante que os marcos retornados pelo LLM estejam no formato de lista de dicionários.
        Aceita tanto listas quanto dicionários e converte automaticamente.
        """
        normalized: List[Dict[str, str]] = []
        if isinstance(raw_milestones, dict):
            for name, timeline in raw_milestones.items():
                normalized.append({
                    "name": str(name),
                    "timeline": str(timeline) if timeline is not None else "Prazo não especificado"
                })
        elif isinstance(raw_milestones, list):
            for item in raw_milestones:
                if isinstance(item, dict):
                    normalized.append({
                        "name": str(item.get("name", "Marco")),
                        "timeline": str(item.get("timeline", item.get("deadline", "Prazo não especificado")))
                    })
                else:
                    normalized.append({
                        "name": str(item),
                        "timeline": "Prazo não especificado"
                    })
        else:
            logger.warning("AGPAgent: 'milestones' retornado em formato inesperado. Aplicando fallback.")
        if not normalized:
            normalized.append({"name": "Planejamento inicial", "timeline": "A definir"})
        return normalized

    def _normalize_resource_needs(self, raw_resources: Any) -> List[str]:
        if isinstance(raw_resources, list):
            return [str(item) for item in raw_resources if str(item).strip()]
        if raw_resources is None:
            return []
        if isinstance(raw_resources, str):
            return [raw_resources]
        return [str(raw_resources)]

    def _normalize_estimate_payload(self, payload: Dict[str, Any]) -> AGPEstimateOutput:
        estimated_time = str(payload.get("estimated_time", "Não informado")).strip()

        estimated_cost_raw = payload.get("estimated_cost", 0.0)
        estimated_cost: float
        if isinstance(estimated_cost_raw, (int, float)):
            estimated_cost = float(estimated_cost_raw)
        else:
            cleaned = str(estimated_cost_raw).replace("R$", "").replace(".", "").replace(",", ".")
            try:
                estimated_cost = float(cleaned)
            except ValueError:
                logger.warning(f"AGPAgent: Não foi possível converter estimated_cost '{estimated_cost_raw}'. Usando 0.0.")
                estimated_cost = 0.0

        milestones = self._normalize_milestones(payload.get("milestones"))
        resource_needs = self._normalize_resource_needs(payload.get("resource_needs"))

        try:
            return AGPEstimateOutput(
                estimated_time=estimated_time or "Não informado",
                estimated_cost=estimated_cost,
                milestones=milestones,
                resource_needs=resource_needs or ["Equipe a definir"]
            )
        except ValidationError as ve:
            logger.error(f"AGPAgent: Falha ao validar dados normalizados: {ve}")
            raise LLMGenerationError(f"Dados normalizados inválidos para estimativa: {ve}") from ve

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
            self._append_schema_instruction(messages)
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                json_mode=True
            )
            raw_content = response_raw.get('content') if isinstance(response_raw, dict) else None
            if not raw_content:
                raise LLMGenerationError("LLM não retornou conteúdo ao estimar projeto.")

            try:
                payload = json.loads(raw_content)
            except json.JSONDecodeError as jde:
                raise LLMGenerationError(f"LLM não retornou JSON válido para estimativa: {jde}") from jde

            normalized_output = self._normalize_estimate_payload(payload)

            logger.info(f"AGPAgent: Estimativa de projeto gerada com sucesso usando {self.model_name}.")
            return normalized_output.model_dump()
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AGPAgent: Falha ao estimar projeto com o LLM {self.model_name}. Erro: {e}")
            return {"error": str(e), "message": f"Falha na estimativa de projeto: {e}", "estimated_time": "(Erro)", "estimated_cost": 0.0}
        except Exception as e:
            logger.error(f"AGPAgent: Erro inesperado ao estimar projeto: {e}")
            return {"error": str(e), "message": f"Erro inesperado na estimativa de projeto: {e}", "estimated_time": "(Erro inesperado)", "estimated_cost": 0.0}
