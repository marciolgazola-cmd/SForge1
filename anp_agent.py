# anp_agent.py

import datetime
import random
import json # Para lidar com a serialização/desserialização de listas no DB
from typing import List, Dict, Any

from data_models import Requirement, Proposal, MoaiLog
from database_manager import DatabaseManager
from llm_simulator import LLMSimulator

class ANPAgent:
    """
    Agente de Negócios e Propostas (ANP)
    Responsável por gerar propostas comerciais detalhadas a partir dos requisitos.
    Agora integrado com DatabaseManager e LLMSimulator.
    """
    def __init__(self, db_manager: DatabaseManager, llm_simulator: LLMSimulator):
        self.db_manager = db_manager
        self.llm_simulator = llm_simulator

    def generate_commercial_proposal(self, requirement: Requirement) -> Proposal:
        """
        Gera uma proposta comercial completa baseada nos requisitos do cliente,
        usando o LLMSimulator e persistindo no banco de dados.
        """
        # 1. MOAI LOG: ANP acionado para gerar proposta
        moai_log_obj = MoaiLog(action="ANP_ACTION", details={"event": "ANP acionado para gerar proposta", "requirement_id": requirement.db_id, "project_name": requirement.nome_projeto})
        moai_log_data_for_db = moai_log_obj.to_dict()
        moai_log_data_for_db.pop('db_id', None) # CORREÇÃO: Remove db_id antes de inserir
        self.db_manager.insert("moai_logs", moai_log_data_for_db)

        # 2. Gerar conteúdo da proposta usando o LLMSimulator
        llm_generated_content = self.llm_simulator.generate_proposal_content(requirement.to_dict())

        # 3. Gerar ID da proposta (simulação)
        # Contagem de propostas existentes para gerar um ID sequencial
        all_proposals = self.db_manager.fetch_all("proposals")
        proposal_id_counter = len(all_proposals) + 1
        proposal_id = f"PROP-{proposal_id_counter:03d}"

        # 4. Definir estimativas (mock, ou poderiam vir do LLM/outro agente AGP)
        # CORREÇÃO: Removido '\' para evitar SyntaxWarning
        valor_estimado = f"R${(proposal_id_counter * 15000 + random.randint(25000, 75000)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        prazo_estimado = f"{proposal_id_counter * 2 + random.randint(6, 12)} semanas"

        # 5. Criar objeto Proposal
        new_proposal = Proposal(
            proposal_id=proposal_id,
            status="Pendente de Aprovação",
            data_geracao=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            titulo=f"Proposta Comercial - {requirement.nome_projeto} para {requirement.nome_cliente}",
            resumo=f"Esta proposta detalha a solução para o problema de negócio de '{requirement.nome_cliente}' visando '{requirement.objetivos_projeto}'.",
            valor_estimado=valor_estimado,
            prazo_estimado=prazo_estimado,
            entendimento_problema=llm_generated_content["entendimento_problema"],
            solucao_proposta=llm_generated_content["solucao_proposta"],
            escopo=llm_generated_content["escopo"],
            tecnologias_sugeridas=llm_generated_content["tecnologias_sugeridas"],
            termos_condicoes=llm_generated_content["termos_condicoes"],
            requirement_id=requirement.db_id,
            requisitos_base=requirement # Associa o objeto Requirement completo para fácil acesso
        )

        # 6. Persistir a proposta no banco de dados
        # O .to_dict() do Proposal precisa ser adaptado para o DB, especialmente listas
        proposal_data_for_db = new_proposal.to_dict()
        proposal_data_for_db.pop('db_id', None) # Remove db_id antes de inserir, pois é auto increment
        proposal_data_for_db.pop('requisitos_base', None) # Não persiste o objeto Requirement completo aqui
        
        # Converte listas para strings JSON para serem armazenadas no DB
        proposal_data_for_db['escopo'] = json.dumps(new_proposal.escopo)
        proposal_data_for_db['tecnologias_sugeridas'] = json.dumps(new_proposal.tecnologias_sugeridas)

        proposal_db_id = self.db_manager.insert("proposals", proposal_data_for_db)
        new_proposal.db_id = proposal_db_id # Atualiza o objeto com o ID do DB

        # 7. MOAI LOG: Proposta gerada e salva
        moai_log_obj = MoaiLog(action="ANP_SUCCESS", details={"event": "Proposta comercial gerada e salva", "proposal_db_id": proposal_db_id, "proposal_id": new_proposal.proposal_id})
        moai_log_data_for_db = moai_log_obj.to_dict()
        moai_log_data_for_db.pop('db_id', None) # CORREÇÃO: Remove db_id antes de inserir
        self.db_manager.insert("moai_logs", moai_log_data_for_db)

        return new_proposal

