"""Module for managing requirement-to-code mappings."""

import json
import logging
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CodeReference:
    """Reference to a code location implementing a requirement."""
    file: str
    line: int
    function: str
    type: str = "implementation"  # "implementation" or "test"

class RequirementsMapper:
    """Manages mappings between requirements and their code implementations."""
    
    def __init__(self, workspace_dir: str = "/work"):
        """Initialize the mapper with workspace directory."""
        self.workspace_dir = Path(workspace_dir)
        self.mapping_file = self.workspace_dir / "requirements_map.json"
        self.mappings: Dict[str, List[CodeReference]] = {}
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load mappings from file if it exists."""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file) as f:
                    data = json.load(f)
                    self.mappings = {
                        req_id: [CodeReference(**ref) for ref in refs]
                        for req_id, refs in data.items()
                    }
                logger.info(f"Loaded {len(self.mappings)} requirement mappings")
            except Exception as e:
                logger.error(f"Error loading mappings: {str(e)}")
                self.mappings = {}

    def _save_mappings(self) -> None:
        """Save mappings to file."""
        try:
            data = {
                req_id: [vars(ref) for ref in refs]
                for req_id, refs in self.mappings.items()
            }
            with open(self.mapping_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.mappings)} requirement mappings")
        except Exception as e:
            logger.error(f"Error saving mappings: {str(e)}")

    def add_mapping(self, requirement_id: str, code_ref: CodeReference) -> None:
        """Add a new code reference for a requirement."""
        if requirement_id not in self.mappings:
            self.mappings[requirement_id] = []
        self.mappings[requirement_id].append(code_ref)
        self._save_mappings()

    def get_references(self, requirement_id: str) -> List[CodeReference]:
        """Get all code references for a requirement."""
        return self.mappings.get(requirement_id, [])

    def clear_references(self, requirement_id: str) -> None:
        """Clear all code references for a requirement."""
        if requirement_id in self.mappings:
            del self.mappings[requirement_id]
            self._save_mappings()

    def scan_code_for_references(self) -> None:
        """Scan code files for requirement references and update mappings."""
        self.mappings.clear()
        
        # Scan implementation files
        impl_dir = self.workspace_dir / "generated"
        if impl_dir.exists():
            for file in impl_dir.rglob("*.py"):
                self._scan_file(file)
        
        self._save_mappings()

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for requirement references."""
        try:
            with open(file_path) as f:
                lines = f.readlines()
                
            current_req = None
            current_func = None
            
            for i, line in enumerate(lines, start=1):
                # Look for requirement tags
                if "# Requirement:" in line:
                    current_req = line.split("# Requirement:")[1].strip()
                
                # Look for function definitions
                elif line.strip().startswith("def ") and current_req:
                    current_func = line.strip().split("def ")[1].split("(")[0]
                    ref = CodeReference(
                        file=str(file_path.relative_to(self.workspace_dir)),
                        line=i,
                        function=current_func
                    )
                    self.add_mapping(current_req, ref)
                    current_req = None
                    current_func = None
                
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {str(e)}")

    def get_vscode_url(self, code_ref: CodeReference) -> str:
        """Generate VS Code Server URL for a code reference."""
        # Create the payload for opening the file at the specific line
        file_path = f"vscode-remote:///work/{code_ref.file}:{code_ref.line}:1"
        payload = f'[["gotoLineMode","true"],["openFile","{file_path}"]]'
        
        return f"http://localhost:8080/?folder=/work&payload={payload}" 