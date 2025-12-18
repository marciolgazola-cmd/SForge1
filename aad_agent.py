# aad_agent.py
import logging
import json # Adicionado
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ValidationError
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

    def _append_schema_instruction(self, messages: list[Dict[str, str]]):
        schema = AADSolutionOutput.model_json_schema()
        llm_schema_instruction = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }
        schema_str = json.dumps(llm_schema_instruction, indent=2, ensure_ascii=False)
        instruction = (
            "\n\nIMPORTANTE: Responda estritamente em JSON preenchendo TODOS os campos abaixo com detalhes técnicos "
            "sobre a arquitetura. Não deixe valores vazios.\n"
            f"{schema_str}\n"
        )
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += instruction
        else:
            messages.append({"role": "user", "content": instruction})

    def _normalize_text(self, value: Any, default: str) -> str:
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

    def _normalize_tech_stack(self, raw_stack: Any) -> List[str]:
        if isinstance(raw_stack, list):
            return [str(item).strip() for item in raw_stack if str(item).strip()]
        if isinstance(raw_stack, str):
            items = [item.strip() for item in raw_stack.split(",") if item.strip()]
            return items if items else ["Tecnologia a definir"]
        if raw_stack is None:
            return ["Tecnologia a definir"]
        return [str(raw_stack)]

    def _normalize_modules(self, raw_modules: Any) -> List[Dict[str, str]]:
        normalized: List[Dict[str, str]] = []
        if isinstance(raw_modules, list):
            for item in raw_modules:
                if isinstance(item, dict):
                    normalized.append({
                        "name": str(item.get("name", item.get("module", "Módulo"))),
                        "responsibility": self._normalize_text(item.get("responsibility"), "Responsabilidade a definir")
                    })
                else:
                    normalized.append({
                        "name": str(item),
                        "responsibility": "Responsabilidade a definir"
                    })
        elif isinstance(raw_modules, dict):
            for name, desc in raw_modules.items():
                normalized.append({
                    "name": str(name),
                    "responsibility": self._normalize_text(desc, "Responsabilidade a definir")
                })
        else:
            logger.warning("AADAgent: 'modules' retornado em formato inesperado. Aplicando fallback.")

        if not normalized:
            normalized.append({"name": "Módulo Principal", "responsibility": "Definir responsabilidades."})
        return normalized

    def _normalize_solution_payload(self, payload: Dict[str, Any]) -> AADSolutionOutput:
        normalized = {
            "architecture_overview": self._normalize_text(payload.get("architecture_overview"), "Arquitetura não informada."),
            "tech_stack": self._normalize_tech_stack(payload.get("tech_stack")),
            "modules": self._normalize_modules(payload.get("modules")),
            "diagram_description": self._normalize_text(payload.get("diagram_description"), "Descrição do diagrama a definir.")
        }
        try:
            return AADSolutionOutput(**normalized)
        except ValidationError as ve:
            logger.error(f"AADAgent: Falha ao validar dados normalizados: {ve}")
            raise LLMGenerationError(f"Dados normalizados inválidos para design da solução: {ve}") from ve

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
            self._append_schema_instruction(messages)
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                json_mode=True
            )
            raw_content = response_raw.get('content') if isinstance(response_raw, dict) else None
            if not raw_content:
                raise LLMGenerationError("LLM não retornou conteúdo ao projetar solução.")

            try:
                payload = json.loads(raw_content)
            except json.JSONDecodeError as jde:
                raise LLMGenerationError(f"LLM não retornou JSON válido para design da solução: {jde}") from jde

            normalized_output = self._normalize_solution_payload(payload)

            logger.info(f"AADAgent: Solução projetada com sucesso usando {self.model_name}.")
            return normalized_output.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AADAgent: Falha ao projetar solução com o LLM {self.model_name}. Erro: {e}")
            return {"error": str(e), "message": f"Falha no design da solução: {e}", "architecture_overview": "(Erro no design)"}
        except Exception as e:
            logger.error(f"AADAgent: Erro inesperado ao projetar solução: {e}")
            return {"error": str(e), "message": f"Erro inesperado no design da solução: {e}", "architecture_overview": "(Erro inesperado)"}
