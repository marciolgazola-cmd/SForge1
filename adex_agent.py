# adex_agent.py
import logging
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ValidationError
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o ADE-X
class GeneratedCodeOutput(BaseModel):
    filename: str = Field(description="Nome do arquivo gerado (ex: 'main.py').")
    language: str = Field(description="Linguagem de programação (ex: 'Python', 'JavaScript').")
    content: str = Field(description="O conteúdo do código gerado.")
    description: str = Field(description="Descrição do propósito do código.")

class ADEXAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('ADE-X') # Obtém o modelo para ADE-X
        logger.info(f"ADEXAgent inicializado com modelo {self.model_name} e pronto para gerar código.")

    def _append_schema_instruction(self, messages: List[Dict[str, str]]):
        schema = GeneratedCodeOutput.model_json_schema()
        llm_schema_instruction = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }
        schema_str = json.dumps(llm_schema_instruction, indent=2, ensure_ascii=False)
        instruction = (
            "\n\nIMPORTANTE: Responda com um JSON COMPLETO seguindo o esquema abaixo. "
            "Inclua nome de arquivo descritivo, linguagem, descrição e código funcional extenso "
            "com comentários e boas práticas.\n"
            f"{schema_str}\n"
        )
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += instruction
        else:
            messages.append({"role": "user", "content": instruction})

    def _normalize_generated_code(self, payload: Dict[str, Any], fallback_description: str) -> GeneratedCodeOutput:
        filename = str(payload.get("filename") or "main.py").strip()
        language = str(payload.get("language") or "Python").strip()
        description = str(payload.get("description") or fallback_description).strip()
        content = payload.get("content")
        if not isinstance(content, str) or len(content.strip()) < 40:
            raise LLMGenerationError("Código gerado foi muito curto ou inválido.")
        try:
            return GeneratedCodeOutput(
                filename=filename or "main.py",
                language=language or "Python",
                content=content,
                description=description or fallback_description
            )
        except ValidationError as ve:
            raise LLMGenerationError(f"Código gerado não respeitou o esquema: {ve}") from ve

    def generate_code(self, project_name: str, client_name: str, code_description: str) -> Dict[str, Any]:
        """
        Gera um snippet de código com base na descrição fornecida.
        """
        prompt = f"""
        Gere um snippet de código {code_description} para o projeto '{project_name}' do cliente '{client_name}'.
        O código deve ser funcional e seguir boas práticas.
        Forneça o nome do arquivo, a linguagem, o conteúdo do código e uma breve descrição.

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Desenvolvimento (ADE-X). Sua tarefa é gerar código-fonte de alta qualidade em diversas linguagens."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para GeneratedCodeOutput."},
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
                raise LLMGenerationError("LLM não retornou conteúdo ao gerar código.")

            try:
                payload = json.loads(raw_content)
            except json.JSONDecodeError as jde:
                raise LLMGenerationError(f"LLM não retornou JSON válido para código: {jde}") from jde

            normalized_output = self._normalize_generated_code(payload, code_description)

            logger.info(f"ADEXAgent: Código gerado com sucesso usando {self.model_name} para '{project_name}'.")
            return normalized_output.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"ADEXAgent: Falha ao gerar código com o LLM {self.model_name}. Erro: {e}")
            return {"error": str(e), "message": f"Falha na geração de código: {e}", "filename": "error.txt", "language": "text", "content": "# Erro ao gerar código", "description": ""}
        except Exception as e:
            logger.error(f"ADEXAgent: Erro inesperado ao gerar código: {e}")
            return {"error": str(e), "message": f"Erro inesperado na geração de código: {e}", "filename": "error.txt", "language": "text", "content": "# Erro inesperado", "description": ""}

