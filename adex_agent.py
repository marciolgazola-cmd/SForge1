# adex_agent.py
import logging
import json # Adicionado
from typing import Dict, Any, List, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
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
            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=GeneratedCodeOutput,
                json_mode=True
            )
            response: GeneratedCodeOutput = cast(GeneratedCodeOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"ADEXAgent: Código gerado com sucesso usando {self.model_name} para '{project_name}'.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"ADEXAgent: Falha ao gerar código com o LLM {self.model_name}. Erro: {e}")
            return {"error": str(e), "message": f"Falha na geração de código: {e}", "filename": "error.txt", "language": "text", "content": "# Erro ao gerar código", "description": ""}
        except Exception as e:
            logger.error(f"ADEXAgent: Erro inesperado ao gerar código: {e}")
            return {"error": str(e), "message": f"Erro inesperado na geração de código: {e}", "filename": "error.txt", "language": "text", "content": "# Erro inesperado", "description": ""}


