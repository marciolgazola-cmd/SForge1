# aid_agent.py
import logging
import json
import random
import datetime
from typing import Dict, Any, List, cast # Adicionado 'cast'
from pydantic import BaseModel, Field
from llm_simulator import LLMSimulator, LLMConnectionError, LLMGenerationError
from agent_model_mapping import get_agent_model

logger = logging.getLogger(__name__)

# Exemplo de modelo de saída para o AID (status da infraestrutura)
class InfraStatusOutput(BaseModel):
    overall_status: str = Field(description="Status geral da infraestrutura (Operational, Degraded, Critical).")
    resources: Dict[str, Dict[str, str]] = Field(description="Status de recursos específicos (Ex: {'Servidor Web': {'status': 'Operational', 'message': 'OK'}}).")
    last_check: str = Field(description="Timestamp da última verificação.")
    alerts: List[str] = Field(description="Lista de alertas relacionados à infraestrutura.")

class AIDAgent:
    def __init__(self, llm_simulator: LLMSimulator):
        self.llm_simulator = llm_simulator
        self.model_name = get_agent_model('AID') # Obtém o modelo para AID
        logger.info(f"AIDAgent inicializado com modelo {self.model_name} e pronto para gerenciar infraestrutura.")

    def provision_environment(self, project_id: str, project_name: str) -> Dict[str, Any]:
        """
        Simula o provisionamento do ambiente do projeto.
        """
        # Em um cenário real, chamaria ferramentas de IaC
        logger.info(f"AIDAgent: Provisionando ambiente para o projeto '{project_name}' (ID: {project_id})...")
        # LLM pode ser usado para gerar scripts IaC ou planos de provisionamento
        prompt = f"""
        Gere um resumo de um plano de provisionamento de ambiente para o projeto '{project_name}' (ID: {project_id}).
        Inclua passos para criação de pastas, repositórios e configuração de recursos em nuvem (simulado).
        """
        messages = [
            {"role": "system", "content": "Você é um Agente de Infraestrutura e DevOps (AID). Sua tarefa é provisionar e gerenciar ambientes."
                                                "Forneça um plano conciso em formato de texto."},
            {"role": "user", "content": prompt}
        ]
        try:
            # LLMSimulator.chat sem response_model retorna Dict[str, Any] com a chave 'content'
            response_raw = self.llm_simulator.chat(messages=messages, model=self.model_name)
            response: Dict[str, Any] = cast(Dict[str, Any], response_raw) # Explicitamente informa ao Pylance que é um dicionário
            logger.info(f"AIDAgent: Ambiente provisionado com sucesso para '{project_name}' usando {self.model_name}.")
            return {"success": True, "message": f"Ambiente provisionado. Detalhes: {response.get('content', 'N/A')}"}
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AIDAgent: Falha ao provisionar ambiente com o LLM {self.model_name}. Erro: {e}")
            return {"success": False, "message": f"Falha no provisionamento do ambiente devido a erro LLM: {e}"}
        except Exception as e:
            logger.error(f"AIDAgent: Erro inesperado no provisionamento do ambiente: {e}")
            return {"success": False, "message": f"Erro inesperado no provisionamento do ambiente: {e}"}

    def configure_backups(self, project_id: str, project_name: str) -> Dict[str, Any]:
        """
        Simula a configuração de rotinas de backup para o projeto.
        Retorna também o status atual dos backups.
        """
        # Em um cenário real, configuraria políticas de backup
        logger.info(f"AIDAgent: Configurando backups para o projeto '{project_name}' (ID: {project_id})...")
        
        # LLM pode ser usado para gerar a política de backup ou validar a configuração
        prompt = f"""
        Descreva uma política de backup para o projeto '{project_name}' (ID: {project_id}),
        incluindo frequência, retenção e tipos de dados. Forneça também um status simulado.
        """
        messages = [
            {"role": "system", "content": "Você é um Agente de Infraestrutura e DevOps (AID). Sua tarefa é gerenciar backups e recuperação de desastres."
                                                "Forneça a política e o status em formato de texto."},
            {"role": "user", "content": prompt}
        ]
        try:
            # LLMSimulator.chat sem response_model retorna Dict[str, Any] com a chave 'content'
            response_raw = self.llm_simulator.chat(messages=messages, model=self.model_name)
            response: Dict[str, Any] = cast(Dict[str, Any], response_raw) # Explicitamente informa ao Pylance que é um dicionário
            logger.info(f"AIDAgent: Backups configurados com sucesso para '{project_name}' usando {self.model_name}.")
            return {
                "success": True,
                "message": f"Backups configurados e status obtido. Detalhes: {response.get('content', 'N/A')}",
                "details": { # Exemplo de detalhes retornados
                    "policy_data": "Diário, retenção de 7 dias, dados e código.",
                    "last_backup_status": random.choice(["Success", "Failed"]),
                    "next_scheduled_backup": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AIDAgent: Falha ao configurar backups com o LLM {self.model_name}. Erro: {e}")
            return {"success": False, "message": f"Falha na configuração de backups devido a erro LLM: {e}"}
        except Exception as e:
            logger.error(f"AIDAgent: Erro inesperado na configuração de backups: {e}")
            return {"success": False, "message": f"Erro inesperado na configuração de backups: {e}"}

    def get_infrastructure_status(self, project_id: str) -> Dict[str, Any]:
        """
        Simula a obtenção do status da infraestrutura de um projeto.
        """
        # Em um cenário real, consultaria ferramentas de monitoramento
        logger.info(f"AIDAgent: Obtendo status da infraestrutura para o projeto (ID: {project_id})...")
        
        prompt = f"""
        Gere um resumo do status atual da infraestrutura para o projeto (ID: {project_id}).
        Inclua o status geral, status de recursos chave como servidor web e banco de dados,
        timestamp da última verificação e quaisquer alertas.

        Sua resposta deve ser um objeto JSON.
        """

        messages = [
            {"role": "system", "content": "Você é um Agente de Infraestrutura e DevOps (AID). Sua tarefa é monitorar e reportar o status da infraestrutura."
                                                "Sua saída deve ser um JSON estritamente no formato do esquema Pydantic para InfraStatusOutput."},
            {"role": "user", "content": prompt}
        ]

        try:
            # Passa o nome do modelo explicitamente e força json_mode
            response_raw = self.llm_simulator.chat(
                messages=messages,
                model=self.model_name,
                response_model=InfraStatusOutput,
                json_mode=True
            )
            response: InfraStatusOutput = cast(InfraStatusOutput, response_raw) # Cast para informar o Pylance
            logger.info(f"AIDAgent: Status da infraestrutura obtido com sucesso usando {self.model_name} para {project_id}.")
            return response.model_dump() # Converte o modelo Pydantic para dicionário
        except (LLMConnectionError, LLMGenerationError) as e:
            logger.error(f"AIDAgent: Falha ao obter status da infraestrutura com o LLM {self.model_name}. Erro: {e}")
            return {"error": str(e), "overall_status": "Critical", "resources": {}, "last_check": datetime.datetime.now().isoformat(), "alerts": [f"Falha ao obter status: {e}"]}
        except Exception as e:
            logger.error(f"AIDAgent: Erro inesperado ao obter status da infraestrutura: {e}")
            return {"error": str(e), "overall_status": "Critical", "resources": {}, "last_check": datetime.datetime.now().isoformat(), "alerts": [f"Erro inesperado: {e}"]}

    def trigger_manual_backup(self, project_id: str) -> Dict[str, Any]:
        """
        Simula o acionamento de um backup manual.
        """
        logger.info(f"AIDAgent: Acionando backup manual para o projeto (ID: {project_id})...")
        # Simula o resultado de uma operação de backup
        success = random.choice([True, False])
        if success:
            message = "Backup manual concluído com sucesso."
            logger.info(f"AIDAgent: {message}")
        else:
            message = "Falha no backup manual. Verifique os logs."
            logger.error(f"AIDAgent: {message}")
        return {"success": success, "message": message}

    def schedule_test_restore(self, project_id: str) -> Dict[str, Any]:
        """
        Simula o agendamento de um teste de restauração de backup.
        """
        logger.info(f"AIDAgent: Agendando teste de restauração para o projeto (ID: {project_id})...")
        # Simula o agendamento
        test_time = datetime.datetime.now() + datetime.timedelta(hours=random.randint(1, 24))
        message = f"Teste de restauração agendado para {test_time.strftime('%Y-%m-%d %H:%M:%S')}."
        logger.info(f"AIDAgent: {message}")
        return {"success": True, "message": message}
