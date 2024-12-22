"""Module for managing requirement-to-code mappings."""

import json
import logging
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import yaml
import traceback
import os

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
        logger.info("Starting code reference scan")
        self.mappings.clear()
        
        # Load settings to get source folder and patterns
        settings_path = self.workspace_dir / "plm_settings.yaml"
        try:
            with open(settings_path) as f:
                settings = yaml.safe_load(f)
                source_folder = settings.get('source_folder', 'src')
                include_patterns = settings.get('source_include_patterns', ['**/*.py', '**/*.cpp', '**/*.hpp', '**/*.h'])
        except Exception as e:
            logger.warning(f"Could not load settings, using defaults: {e}")
            source_folder = 'src'
            include_patterns = ['**/*.py', '**/*.cpp', '**/*.hpp', '**/*.h']
        
        # Scan source directory
        source_dir = self.workspace_dir / source_folder
        logger.info(f"Scanning directory: {source_dir}")
        
        if source_dir.exists():
            for pattern in include_patterns:
                logger.debug(f"Scanning for pattern: {pattern}")
                try:
                    # Split pattern into parts and handle ** separately
                    parts = pattern.split('/')
                    if len(parts) == 1:
                        # Single pattern like "*.py"
                        for file in source_dir.rglob(parts[0]):
                            if file.is_file():
                                logger.debug(f"Scanning file: {file}")
                                self._scan_file(file)
                    else:
                        # Complex pattern with directories
                        base = source_dir
                        for file in base.glob(pattern):
                            if file.is_file():
                                logger.debug(f"Scanning file: {file}")
                                self._scan_file(file)
                except ValueError as e:
                    logger.warning(f"Skipping invalid pattern {pattern}: {e}")
                    continue
        
        self._save_mappings()
        logger.info(f"Code reference scan complete. Found {len(self.mappings)} requirement references")

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for requirement references."""
        try:
            logger.debug(f"Scanning file: {file_path}")
            with open(file_path) as f:
                lines = f.readlines()
                
            current_req = None
            current_func = None
            
            for i, line in enumerate(lines, start=1):
                line = line.strip()
                
                # Look for requirement tags in various formats
                req_indicators = [
                    "# Requirement:", "// Requirement:", "/* Requirement:",
                    "@requirement", "@req", "RQ-"
                ]
                
                for indicator in req_indicators:
                    if indicator in line:
                        # Extract requirement ID
                        if "RQ-" in line:
                            # Find the RQ- pattern and extract the full ID
                            import re
                            match = re.search(r'RQ-[A-Z_]+(?:-|\w)*\d+', line)
                            if match:
                                current_req = match.group(0)
                                logger.debug(f"Found requirement reference: {current_req}")
                        else:
                            # Extract requirement ID after the indicator
                            parts = line.split(indicator)
                            if len(parts) > 1:
                                current_req = parts[1].strip().split()[0].strip(':"*/')
                                logger.debug(f"Found requirement reference: {current_req}")
                
                # Look for function/method definitions
                if current_req:
                    # C++ class method or function
                    if (line.startswith("void ") or 
                        line.startswith("int ") or 
                        line.startswith("bool ") or 
                        line.startswith("string ") or
                        "::" in line or
                        line.startswith("class ") or
                        line.startswith("struct ")):
                        
                        # Extract function/class name
                        if "::" in line:  # Class method
                            current_func = line.split("::")[1].split("(")[0].strip()
                        else:  # Function or class
                            current_func = line.split(" ")[1].split("(")[0].strip()
                        
                        ref = CodeReference(
                            file=str(file_path.relative_to(self.workspace_dir)),
                            line=i,
                            function=current_func,
                            type="implementation"
                        )
                        self.add_mapping(current_req, ref)
                        logger.debug(f"Added mapping: {current_req} -> {ref.file}:{ref.line}")
                    
                    # Python function
                    elif line.startswith("def "):
                        current_func = line.strip().split("def ")[1].split("(")[0]
                        ref = CodeReference(
                            file=str(file_path.relative_to(self.workspace_dir)),
                            line=i,
                            function=current_func,
                            type="implementation"
                        )
                        self.add_mapping(current_req, ref)
                        logger.debug(f"Added mapping: {current_req} -> {ref.file}:{ref.line}")
                
                # Reset requirement if we hit a blank line or end of function
                if not line or line.startswith("}"):
                    current_req = None
                    current_func = None
                
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    def get_vscode_url(self, ref: CodeReference) -> str:
        """Generate a URL for opening the reference in VSCode/code-server."""
        # Use the relative path directly from the CodeReference
        # ref.file is already relative to the workspace
        file_path = ref.file
        line_number = ref.line
        
        # Create payload without URL encoding
        payload = [
            ['gotoLineMode', 'true'],
            ['openFile', f'vscode-remote:///work/{file_path}:{line_number}:1']
        ]
        
        # Create URL without encoding the payload
        url = f"http://localhost:8080/?folder=/work&payload={str(payload)}"
        logger.info(f"Generated VSCode URL (backend): {url}")
        return url

    def add_requirement_reference(self, requirement_id: str, file_path: str, line_number: int = 1) -> None:
        """Add a requirement reference to a source file."""
        try:
            full_path = self.workspace_dir / file_path
            if not full_path.exists():
                logger.warning(f"File not found: {full_path}")
                return

            # Read the file content
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Determine the file type and appropriate comment style
            ext = full_path.suffix.lower()
            if ext in ['.cpp', '.hpp', '.h']:
                comment_start = '// '
            elif ext in ['.py']:
                comment_start = '# '
            elif ext in ['.ts', '.tsx', '.js', '.jsx']:
                comment_start = '// '
            else:
                comment_start = '// '

            # Create the requirement reference comment
            reference = f"{comment_start}Requirement: {requirement_id}\n"

            # Check if the requirement reference already exists
            if any(requirement_id in line for line in lines):
                logger.debug(f"Requirement {requirement_id} already referenced in {file_path}")
                return

            # Find appropriate insertion point (before function/class definition)
            insert_line = line_number
            while insert_line > 1 and any(keyword in lines[insert_line-1].lower() 
                for keyword in ['class', 'struct', 'void', 'int', 'bool', 'def', 'function', 'interface']):
                insert_line -= 1

            # Insert the reference
            if insert_line <= len(lines):
                lines.insert(insert_line - 1, reference)
            else:
                lines.append('\n' + reference)

            # Write back to file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            # Add to mappings
            code_ref = CodeReference(
                file=str(file_path),
                line=insert_line,
                function="",  # Will be updated by scan_code_for_references
                type="implementation"
            )
            self.add_mapping(requirement_id, code_ref)

            logger.info(f"Added requirement reference to {file_path} at line {insert_line}")

            # Rescan the file to update function information
            self._scan_file(full_path)

        except Exception as e:
            logger.error(f"Error adding requirement reference to {file_path}: {e}")
            logger.error(traceback.format_exc())