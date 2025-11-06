# ade_x_agent.py

import datetime
import random
from typing import List, Dict
import json

from data_models import Project, Requirement, GeneratedCode, MoaiLog
from database_manager import DatabaseManager
from llm_simulator import LLMSimulator

class ADEXAgent:
    """
    Agentes de Desenvolvimento (ADE-X)
    Responsáveis por gerar código-fonte de acordo com os requisitos do projeto
    e a arquitetura definida. Agora integrado com DatabaseManager e LLMSimulator.
    """
    def __init__(self, db_manager: DatabaseManager, llm_simulator: LLMSimulator):
        self.db_manager = db_manager
        self.llm_simulator = llm_simulator

    def generate_code_for_project(self, project: Project, requirement: Requirement) -> List[GeneratedCode]:
        """
        Simula a geração de diversos arquivos de código para um projeto,
        usando o LLMSimulator e persistindo no banco de dados.
        """
        # 1. MOAI LOG: ADE-X acionado para gerar código
        moai_log_obj = MoaiLog(action="ADE-X_ACTION", details={"event": "ADE-X acionado para gerar código", "project_db_id": project.db_id, "project_id": project.project_id})
        moai_log_data_for_db = moai_log_obj.to_dict()
        moai_log_data_for_db.pop('db_id', None) # CORREÇÃO: Remove db_id antes de inserir
        self.db_manager.insert("moai_logs", moai_log_data_for_db)

        # 2. Gerar snippets de código usando o LLMSimulator
        generated_code_data_list = self.llm_simulator.generate_code_snippets(project.name, requirement.to_dict())
        
        generated_code_objects = []
        for code_data in generated_code_data_list:
            # 3. Criar objeto GeneratedCode e persistir
            new_code = GeneratedCode(
                project_db_id=project.db_id,
                filename=code_data['filename'],
                language=code_data['language'],
                content=code_data['content']
            )
            code_data_for_db = new_code.to_dict()
            code_data_for_db.pop('db_id', None) # Remove db_id antes de inserir
            
            code_db_id = self.db_manager.insert("generated_code", code_data_for_db)
            new_code.db_id = code_db_id
            generated_code_objects.append(new_code)
        
        # 4. MOAI LOG: Código gerado e salvo
        moai_log_obj = MoaiLog(action="ADE-X_SUCCESS", details={"event": f"Código gerado e salvo para o projeto {project.project_id}", "num_files": len(generated_code_objects), "project_db_id": project.db_id})
        moai_log_data_for_db = moai_log_obj.to_dict()
        moai_log_data_for_db.pop('db_id', None) # CORREÇÃO: Remove db_id antes de inserir
        self.db_manager.insert("moai_logs", moai_log_data_for_db)

        return generated_code_objects
