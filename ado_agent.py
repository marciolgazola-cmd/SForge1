# ado_agent.py
import uuid
import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelo Pydantic para a resposta do ADO ---
class ADOResponse(BaseModel):
    filename: Optional[str] = Field(None, description="Nome do arquivo da documentação gerada.")
    content: Optional[str] = Field(None, description="Conteúdo completo da documentação em formato Markdown.")
    document_type: Optional[str] = Field(None, description="Tipo de documento (ex: 'Manual do Usuário', 'Documentação Técnica').")
    version: Optional[str] = Field("1.0", description="Versão do documento.")
    last_updated: Optional[str] = Field(None, description="Data e hora da última atualização.")

class ADOAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model = get_agent_model('ADO')  # mistral para documentação clara
        logging.info(f"ADOAgent inicializado com modelo {self.model} e pronto para documentar projetos.")

    def generate_documentation(self, project_id: str, project_name: str, doc_type: str, relevant_info: str) -> Dict[str, Any]:
        logging.info(f"ADOAgent: Gerando documentação '{doc_type}' para o projeto '{project_name}' ({project_id})...")

        prompt = f"""
        Gere uma documentação do tipo '{doc_type}' para o projeto '{project_name}' (ID: {project_id}).
        Utilize as informações relevantes fornecidas para criar um documento completo e claro em formato Markdown.

        Informações Relevantes:
        {relevant_info}

        A documentação deve ser estruturada e fácil de ler.

        Sua resposta deve ser um JSON estritamente conforme o modelo ADOResponse Pydantic.
        """

        system_message = "Você é o Agente de Documentação (ADO) da Synapse Forge. Sua função é criar documentação técnica e de usuário abrangente e clara para os projetos de software, utilizando formato Markdown."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            response_obj = self.llm_simulator.chat(messages, response_model=ADOResponse, model_override=self.model)
            logging.info(f"ADOAgent: Documentação '{doc_type}' gerada para o projeto '{project_name}' ({project_id}).")
            return response_obj.dict()
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"ADOAgent: Falha ao gerar documentação '{doc_type}' para '{project_name}' ({project_id}). Erro: {e}")
            error_message = f"Erro ao gerar documentação com o LLM: {e}. Gerando documento padrão."
            logging.warning(error_message)
            # Fallback para um documento com dados padrão
            return {
                "filename": f"fallback_doc_{uuid.uuid4().hex[:8]}.md",
                "content": f"""
# Documentação Padrão (Erro na Geração)
Não foi possível gerar a documentação detalhada para o projeto '{project_name}'
devido a um erro no LLM.

**Erro:** {e}

Por favor, tente novamente ou verifique a conexão com o LLM.
""",
                "document_type": doc_type,
                "version": "N/A",
                "last_updated": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"ADOAgent: Erro inesperado ao gerar documentação: {e}")
            return {
                "filename": f"internal_error_doc_{uuid.uuid4().hex[:8]}.md",
                "content": f"""
# Documentação Padrão (Erro Interno)
Um erro inesperado ocorreu durante a geração da documentação para o projeto '{project_name}':

**Erro:** {e}
""",
                "document_type": doc_type,
                "version": "N/A",
                "last_updated": datetime.datetime.now().isoformat()
            }
