import json
import os
import platform
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional


class TestWorkspaceManager:
    """
    Cria, registra e remove workspaces temporários para executar snippets
    gerados pelo ADE-X sem impactar o repositório principal.
    """

    def __init__(self, base_dir: Optional[str] = None):
        env_base_dir = os.environ.get("TEST_WORKSPACES_DIR")
        default_base_dir = str(Path.home() / "test_workspaces")
        resolved_base_dir = base_dir or env_base_dir or default_base_dir
        self.base_dir = Path(resolved_base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _detect_requirements(self, content: str, language: str) -> List[str]:
        if language.lower() != "python":
            return []
        reqs = set()
        lowered = content.lower()
        mapping = {
            "fastapi": "fastapi",
            "uvicorn": "uvicorn[standard]",
            "psycopg2": "psycopg2-binary",
            "redis": "redis",
            "pydantic": "pydantic",
            "sqlalchemy": "sqlalchemy",
            "pandas": "pandas",
        }
        for key, requirement in mapping.items():
            if key in lowered:
                reqs.add(requirement)
        # Dependências básicas para projetos web Python
        reqs.update({"python-dotenv"})
        return sorted(reqs)

    def _create_virtualenv(self, workspace_path: Path) -> Path:
        venv_path = workspace_path / ".venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        return venv_path

    def _get_venv_python(self, venv_path: Path) -> Path:
        if os.name == "nt":
            return venv_path / "Scripts" / "python.exe"
        return venv_path / "bin" / "python"

    def _ensure_pyinstaller(self, python_path: Path):
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(python_path), "-m", "pip", "install", "pyinstaller"], check=True)

    def _write_executable_assets(self, workspace_path: Path, filename: str) -> Dict[str, str]:
        exe_name = Path(filename).stem
        unix_script = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$(dirname "$0")"
            source .venv/bin/activate
            python -m pip install --upgrade pip
            python -m pip install pyinstaller
            python -m PyInstaller --onefile --name "{exe_name}" src/{filename}
            """
        ).strip()
        windows_script = textwrap.dedent(
            f"""\
            @echo off
            cd /d %~dp0
            call .venv\\Scripts\\activate
            python -m pip install --upgrade pip
            python -m pip install pyinstaller
            python -m PyInstaller --onefile --name "{exe_name}" src\\{filename}
            """
        ).strip()

        unix_script_path = workspace_path / "build_executable.sh"
        windows_script_path = workspace_path / "build_executable.bat"
        unix_script_path.write_text(unix_script + "\n")
        windows_script_path.write_text(windows_script + "\n")
        try:
            unix_script_path.chmod(0o755)
        except PermissionError:
            pass

        docs = textwrap.dedent(
            f"""
            # Gerar Executavel (Python)

            O executavel precisa ser gerado no mesmo sistema do cliente.

            - Linux/macOS:
              ./build_executable.sh

            - Windows:
              build_executable.bat

            Saida em: dist/{exe_name}
            """
        ).strip()
        docs_path = workspace_path / "BUILD_EXECUTABLE.md"
        docs_path.write_text(docs + "\n")

        return {
            "build_docs_path": str(docs_path),
            "build_script_unix": str(unix_script_path),
            "build_script_windows": str(windows_script_path),
        }

    def prepare_executable(self, workspace_path: str, filename: str, target_os: str) -> Dict[str, str]:
        workspace = Path(workspace_path)
        assets = self._write_executable_assets(workspace, filename)

        normalized_target = (target_os or "").strip().lower()
        if normalized_target in {"mac", "macos", "darwin"}:
            normalized_target = "mac"
        elif normalized_target in {"windows", "win"}:
            normalized_target = "windows"
        elif normalized_target in {"linux"}:
            normalized_target = "linux"
        else:
            normalized_target = ""

        current = platform.system().lower()
        if current.startswith("win"):
            current = "windows"
        elif current.startswith("darwin"):
            current = "mac"
        elif current.startswith("linux"):
            current = "linux"

        if normalized_target and normalized_target != current:
            return {
                "success": False,
                "built": False,
                "message": "Executavel nao gerado: o sistema atual nao corresponde ao sistema do cliente.",
                **assets,
            }

        venv_path = workspace / ".venv"
        if not venv_path.exists():
            venv_path = self._create_virtualenv(workspace)

        python_path = self._get_venv_python(venv_path)
        if not python_path.exists():
            raise FileNotFoundError("Virtualenv python not found.")

        self._ensure_pyinstaller(python_path)

        exe_name = Path(filename).stem
        cmd = [
            str(python_path),
            "-m",
            "PyInstaller",
            "--onefile",
            "--name",
            exe_name,
            f"src/{filename}",
        ]
        subprocess.run(cmd, check=True, cwd=str(workspace))

        output_name = f"{exe_name}.exe" if current == "windows" else exe_name
        output_path = workspace / "dist" / output_name
        return {
            "success": True,
            "built": True,
            "message": "Executavel gerado com sucesso.",
            "output_path": str(output_path),
            **assets,
        }

    def create_workspace(
        self,
        workspace_id: str,
        filename: str,
        content: str,
        language: str,
        description: Optional[str] = None,
    ) -> Dict[str, str]:
        workspace_path = self.base_dir / workspace_id
        if workspace_path.exists():
            raise FileExistsError(f"O workspace {workspace_id} já existe.")
        workspace_path.mkdir(parents=True)

        src_path = workspace_path / "src"
        src_path.mkdir()

        file_path = src_path / filename
        file_path.write_text(content)

        requirements = self._detect_requirements(content, language)
        if requirements:
            (workspace_path / "requirements.txt").write_text("\n".join(requirements) + "\n")

        metadata = {
            "filename": filename,
            "description": description or "",
            "language": language,
        }
        (workspace_path / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

        venv_path = self._create_virtualenv(workspace_path) if language.lower() == "python" else None

        instructions = textwrap.dedent(
            f"""
            # Ambiente de Teste - {workspace_id}
            Diretório: {workspace_path}

            1. Entre na pasta:
               cd {workspace_path}

            2. Ative o virtualenv:
               source .venv/bin/activate

            3. (Opcional) Instale dependências:
               pip install -r requirements.txt

            4. Execute o código:
               python src/{filename}

            5. (Opcional) Gerar executavel:
               Veja BUILD_EXECUTABLE.md
            """
        ).strip()
        (workspace_path / "README_TEST_ENV.md").write_text(instructions)

        requirements_path = workspace_path / "requirements.txt"
        return {
            "workspace_path": str(workspace_path),
            "src_path": str(src_path),
            "file_path": str(file_path),
            "venv_path": str(venv_path) if venv_path else "",
            "requirements_path": str(requirements_path) if requirements_path.exists() else "",
            "instructions": instructions,
        }

    def delete_workspace(self, workspace_path: str):
        path = Path(workspace_path)
        if path.exists():
            shutil.rmtree(path)
