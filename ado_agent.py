# ado_agent.py
import logging
import json
from typing import Dict, Any, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
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
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=DocumentationOutput,
                json_mode=True
            )
            response: DocumentationOutput = cast(DocumentationOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"ADOAgent: Documentação '{doc_type}' gerada com sucesso usando {self.model_name} para '{project_name}'.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
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
