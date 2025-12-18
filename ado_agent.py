# ado_agent.py
import logging
import json
import uuid
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o ADO
class DocumentationOutput(BaseModel):
    filename: str = Field(description="Nome do arquivo da documentação (ex: 'README.md', 'Manual_Usuario.pdf').")
    document_type: str = Field(description="Tipo de documentação (ex: 'Documentação Técnica', 'Manual do Usuário').")
    version: str = Field(description="Versão da documentação.")
    content: str = Field(description="O conteúdo completo da documentação em formato Markdown.")

class ADOAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('ADO') # Obtém o modelo para ADO
        logger.info(f"ADOAgent inicializado com modelo {self.model_name} e pronto para documentar projetos.")

    def _append_schema_instruction(self, messages: list[Dict[str, str]]):
        schema = DocumentationOutput.model_json_schema()
        llm_schema_instruction = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }
        schema_str = json.dumps(llm_schema_instruction, indent=2, ensure_ascii=False)
        instruction = (
            "\n\nIMPORTANTE: Responda em JSON seguindo EXACTAMENTE o esquema abaixo. "
            "Preencha todos os campos com conteúdo detalhado e em português.\n"
            f"{schema_str}\n"
        )
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += instruction
        else:
            messages.append({"role": "user", "content": instruction})

    def _normalize_str_field(self, value: Any, default: str) -> str:
        """
        Converte qualquer valor em string, aplicando um valor padrão se estiver vazio ou None.
        """
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else default
        if value is None:
            return default
        if isinstance(value, (dict, list)):
            try:
                converted = json.dumps(value, ensure_ascii=False, indent=2)
            except Exception:
                converted = str(value)
        else:
            converted = str(value)
        cleaned = converted.strip()
        return cleaned if cleaned else default

    def _build_default_content(self, project_name: str, doc_type: str, relevant_info: str) -> str:
        """
        Gera um conteúdo básico para a documentação caso o LLM não retorne nada útil.
        """
        base_info = relevant_info.strip() if relevant_info else "Informações relevantes não fornecidas."
        return (
            f"# {doc_type} - {project_name}\n\n"
            f"## Visão Geral\n"
            f"{base_info}\n\n"
            f"## Estrutura Inicial\n"
            f"- Objetivos principais\n"
            f"- Arquitetura da solução\n"
            f"- Requisitos técnicos\n"
            f"- Próximos passos\n"
        )

    def generate_documentation(self, project_id: str, project_name: str, doc_type: str, relevant_info: str) -> Dict[str, Any]:
        """
        Gera documentação para um projeto com base no tipo e informações relevantes.
        """
        prompt = f"""
        Gere uma '{doc_type}' detalhada para o projeto '{project_name}' (ID: {project_id}).
        Utilize as informações relevantes fornecidas. A documentação deve ser clara, concisa e formatada em Markdown.

        Informações Relevantes:
        {relevant_info}

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Documentação (ADO). Sua tarefa é criar documentação clara, precisa e atualizada para os projetos."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para DocumentationOutput."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Passa o nome do modelo explicitamente e força json_mode
            self._append_schema_instruction(messages)
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                json_mode=True
            )
            raw_content = response_raw.get('content') if isinstance(response_raw, dict) else None
            if not raw_content:
                raise LLMGenerationError("LLM retornou resposta vazia ao gerar documentação.")

            try:
                doc_payload = json.loads(raw_content)
            except json.JSONDecodeError as je:
                raise LLMGenerationError(f"LLM não retornou JSON válido para documentação: {je}") from je

            normalized_doc = {
                "filename": self._normalize_str_field(doc_payload.get('filename'), f"doc_{uuid.uuid4().hex[:8]}.md"),
                "document_type": self._normalize_str_field(doc_payload.get('document_type'), doc_type),
                "version": self._normalize_str_field(doc_payload.get('version'), "1.0"),
                "content": self._normalize_str_field(doc_payload.get('content'), "")
            }

            if not normalized_doc['content']:
                normalized_doc['content'] = self._build_default_content(project_name, doc_type, relevant_info)

            try:
                response_model = DocumentationOutput(**normalized_doc)
            except ValidationError as ve:
                raise LLMGenerationError(f"Dados normalizados não correspondem ao esquema de documentação: {ve}") from ve

            logger.info(f"ADOAgent: Documentação '{doc_type}' gerada com sucesso usando {self.model_name} para '{project_name}'.")
            return response_model.model_dump()
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"ADOAgent: Falha ao gerar documentação com o LLM {self.model_name}. Erro: {e}")
            # Retorno de fallback consistente com a estrutura esperada
            return {
                "filename": f"fallback_doc_{project_id[:8]}.md",
                "document_type": doc_type,
                "version": "1.0-ERROR",
                "content": f"# Erro na Geração da Documentação\n\nOcorreu um erro ao gerar a documentação com o LLM: {e}\n\nPor favor, verifique a conexão com o LLM ou o modelo configurado."
            }
        except Exception as e:
            logger.error(f"ADOAgent: Erro inesperado ao gerar documentação: {e}")
            return {
                "filename": f"fallback_doc_unexpected_error_{project_id[:8]}.md",
                "document_type": doc_type,
                "version": "1.0-UNEXPECTED_ERROR",
                "content": f"# Erro Inesperado na Geração da Documentação\n\nOcorreu um erro inesperado: {e}\n\nPor favor, contate o suporte técnico."
            }
