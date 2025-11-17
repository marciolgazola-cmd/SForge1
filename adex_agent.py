# adex_agent.py
import uuid
import datetime
import random
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Modelo Pydantic para a resposta de código do ADE-X ---
class ADEXCodeResponse(BaseModel):
    filename: str = Field(..., description="Nome do arquivo de código gerado.")
    language: str = Field(..., description="Linguagem de programação do código (ex: Python, JavaScript).")
    content: str = Field(..., description="Conteúdo do código gerado.")
    description: str = Field(..., description="Breve descrição do que este bloco de código faz.")

class ADEXAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        logging.info("ADEXAgent inicializado e pronto para gerar código.")

    def generate_code(self, project_name: str, client_name: str, task_description: str) -> Dict[str, Any]:
        logging.info(f"ADEXAgent: Iniciando geração de código para '{task_description}' do projeto '{project_name}'...")
        
        prompt = f"""
        Gere um bloco de código de exemplo ou um módulo funcional com base na seguinte descrição de tarefa para o projeto '{project_name}' do cliente '{client_name}'.
        A tarefa é: '{task_description}'.

        A saída deve ser um arquivo Python, mas pode incluir outras linguagens se for parte da tarefa (ex: HTML/CSS/JS para frontend).
        Seja conciso, mas forneça um exemplo funcional.

        Sua resposta deve ser um JSON estritamente conforme o modelo ADEXCodeResponse Pydantic.
        """

        system_message = "Você é o Agente de Desenvolvimento (ADE-X) da Synapse Forge. Sua função é gerar código-fonte de alta qualidade e seguindo as melhores práticas para os projetos de software. Entenda a descrição da tarefa e produza o código correspondente."
        
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        try:
            response_obj = self.llm_simulator.chat(messages, response_model=ADEXCodeResponse)
            logging.info(f"ADEXAgent: Geração de código concluída para '{task_description}' do projeto '{project_name}'.")
            return response_obj.dict()
        except (LLMConnectionError, LLMGenerationError) as e:
            logging.error(f"ADEXAgent: Falha ao gerar código para '{task_description}' do projeto '{project_name}'. Erro: {e}")
            error_message = f"Erro ao gerar código com o LLM: {e}. Gerando código padrão."
            logging.warning(error_message)
            # Fallback para um código de exemplo ou mensagem de erro
            return {
                "filename": f"error_code_{uuid.uuid4().hex[:8]}.py",
                "language": "Python",
                "content": f"""
# Erro na Geração de Código
# Não foi possível gerar o código solicitado devido a um erro no LLM:
# {e}
# Por favor, revise a descrição da tarefa ou verifique a conexão com o LLM.
def placeholder_function():
    pass
""",
                "description": f"Código de fallback devido a erro na geração de código do LLM. {error_message}"
            }
        except Exception as e:
            logging.error(f"ADEXAgent: Erro inesperado ao gerar código: {e}")
            return {
                "filename": f"error_code_internal_{uuid.uuid4().hex[:8]}.py",
                "language": "Python",
                "content": f"""
# Erro Interno na Geração de Código
# Um erro inesperado ocorreu durante a geração de código:
# {e}
""",
                "description": f"Código de fallback devido a erro interno na geração de código. {e}"
            }
