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
import re

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
        # Clear existing mappings before scanning
        self.mappings.clear()
        logger.info("Cleared existing mappings")
        
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
            added_refs = set()  # Track already added references
            
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
                            match = re.search(r'RQ-[A-Z_]+(?:-|\w)*\d+', line)
                            if match:
                                current_req = match.group(0)
                                logger.debug(f"Found requirement reference: {current_req}")
                        else:
                            parts = line.split(indicator)
                            if len(parts) > 1:
                                current_req = parts[1].strip().split()[0].strip(':"*/')
                                logger.debug(f"Found requirement reference: {current_req}")
                
                # Look for function/method definitions
                if current_req:
                    # Enhanced C++ function detection
                    cpp_patterns = [
                        # Class method definition (with or without class name)
                        r'^(?:\w+::)?(\w+)\s*\([^)]*\)\s*(?:const|override|final|noexcept)?\s*(?:=\s*0)?\s*(?:->.*?)?\s*\{?$',
                        # Standard function definition with any return type
                        r'^(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?'
                        r'(?:[\w:]+(?:<[^>]+>)?(?:\s*[&*]+)?)'  # Return type with templates and pointers
                        r'\s+(\w+)\s*\([^)]*\)\s*(?:const|override|final|noexcept)?\s*(?:=\s*0)?\s*(?:->.*?)?\s*\{?$',
                        # Constructor definition with initializer list
                        r'^(\w+)::\1\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{?$',
                        # Class/struct definition with inheritance
                        r'^(?:class|struct)\s+(\w+)(?:\s*:\s*(?:public|protected|private)\s+[^{]+)?\s*\{?$',
                        # Template function or class
                        r'^template\s*<[^>]+>\s*(?:class|struct|[\w:]+(?:\s*[&*]+)?)\s+(\w+)',
                    ]
                    
                    # Python function pattern
                    py_pattern = r'^def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[\w\[\],\s]+)?\s*:'
                    
                    found_func = False
                    
                    # Check C++ patterns
                    for pattern in cpp_patterns:
                        match = re.match(pattern, line)
                        if match:
                            func_name = match.group(1)
                            ref_key = f"{current_req}:{str(file_path)}:{func_name}"
                            
                            if ref_key not in added_refs:  # Only add if not already added
                                ref = CodeReference(
                                    file=str(file_path.relative_to(self.workspace_dir)),
                                    line=i,
                                    function=func_name,
                                    type="implementation"
                                )
                                self.add_mapping(current_req, ref)
                                added_refs.add(ref_key)
                                logger.debug(f"Added mapping: {current_req} -> {ref.file}:{ref.line} ({func_name})")
                            found_func = True
                            break
                    
                    # Check Python pattern if no C++ match
                    if not found_func:
                        match = re.match(py_pattern, line)
                        if match:
                            func_name = match.group(1)
                            ref_key = f"{current_req}:{str(file_path)}:{func_name}"
                            
                            if ref_key not in added_refs:  # Only add if not already added
                                ref = CodeReference(
                                    file=str(file_path.relative_to(self.workspace_dir)),
                                    line=i,
                                    function=func_name,
                                    type="implementation"
                                )
                                self.add_mapping(current_req, ref)
                                added_refs.add(ref_key)
                                logger.debug(f"Added mapping: {current_req} -> {ref.file}:{ref.line} ({func_name})")
                
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

    def _find_function_line(self, file_lines: List[str], function_name: str, start_line: int = 1) -> Optional[int]:
        """Find the exact line number where a function is defined."""
        # C++ function patterns
        cpp_patterns = [
            (r'^(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?'
             r'(?:void|int|bool|char|float|double|auto|string|std::string|\w+::\w+|\w+)'
             r'\s+' + re.escape(function_name) + r'\s*\([^)]*\)\s*(?:const|override|final|noexcept)?\s*(?:=\s*0)?\s*\{?$'),
            r'^(?:class|struct)\s+' + re.escape(function_name) + r'(?:\s*:\s*\w+)?\s*\{?$',
            r'\w+::' + re.escape(function_name) + r'\s*\([^)]*\)\s*(?:const|override|final|noexcept)?\s*(?:=\s*0)?\s*\{?$'
        ]
        
        # Python function pattern
        py_pattern = r'^def\s+' + re.escape(function_name) + r'\s*\([^)]*\)\s*(?:->\s*[\w\[\],\s]+)?\s*:'
        
        # First try looking near the suggested start line
        search_start = max(0, start_line - 10)  # Look 10 lines before
        search_end = min(len(file_lines), start_line + 10)  # and 10 lines after
        
        # First pass - look around the suggested line
        for i in range(search_start, search_end):
            line = file_lines[i].strip()
            
            # Check C++ patterns
            for pattern in cpp_patterns:
                if re.match(pattern, line):
                    return i + 1
            
            # Check Python pattern
            if re.match(py_pattern, line):
                return i + 1
        
        # Second pass - search the entire file if not found near suggested line
        for i, line in enumerate(file_lines):
            line = line.strip()
            
            # Check C++ patterns
            for pattern in cpp_patterns:
                if re.match(pattern, line):
                    return i + 1
            
            # Check Python pattern
            if re.match(py_pattern, line):
                return i + 1
        
        return None

    def add_requirement_reference(self, requirement_id: str, file_path: str, line_number: int = 1, target_function: str = None) -> None:
        """Add a requirement reference to a source file."""
        try:
            # Get code analyzer instance to access analysis results
            from .code_analyzer import CodeAnalyzerService
            analyzer = CodeAnalyzerService()
            
            # Get analysis results for the file
            analysis_results = analyzer.analysis_state.get('results', {}).get(file_path, {})
            functions = analysis_results.get('functions', [])
            
            full_path = self.workspace_dir / file_path
            if not full_path.exists():
                logger.warning(f"File not found: {full_path}")
                return

            # Read the file content
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Determine the file type and appropriate comment style
            ext = full_path.suffix.lower()
            if ext in ['.cpp', '.hpp', '.h', '.ts', '.tsx', '.js', '.jsx']:
                comment_start = '// '
            elif ext in ['.py']:
                comment_start = '# '
            else:
                comment_start = '// '

            # First try to find the target function in analysis results
            found_function = None
            function_start = line_number
            
            logger.info(f"Looking for function in {file_path} (target: {target_function}, line: {line_number})")
            
            # First try to find from analysis results
            for func in functions:
                func_line = getattr(func, 'line_number', None)
                func_end_line = getattr(func, 'end_line', float('inf'))
                func_name = getattr(func, 'name', None)
                
                logger.debug(f"Checking function from analysis: name={func_name}, line={func_line}, end_line={func_end_line}")
                
                # If we have a target function name, only match that specific function
                if target_function and func_name:
                    # Try both with and without class name
                    class_method = func_name.split('::')[-1] if '::' in func_name else func_name
                    if class_method == target_function or func_name == target_function:
                        found_function = func
                        function_start = func_line
                        logger.info(f"Found target function {target_function} at line {func_line}")
                        break
                # Otherwise fall back to line number based matching
                elif not target_function and func_line is not None:
                    # Check if this function is closest to our target line
                    if abs(func_line - line_number) < abs(function_start - line_number):
                        found_function = func
                        function_start = func_line
                        logger.info(f"Found closest function {func_name} at line {func_line}")

            # If not found in analysis, scan manually
            if not found_function:
                logger.info(f"Scanning manually for function {target_function if target_function else 'at line ' + str(line_number)}")
                # Enhanced C++ patterns
                cpp_patterns = [
                    # Class method definition (with or without class name)
                    r'^(?:\w+::)?(\w+)\s*\([^)]*\)\s*(?:const|override|final|noexcept)?\s*(?:=\s*0)?\s*(?:->.*?)?\s*\{?$',
                    # Standard function definition with any return type
                    r'^(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?'
                    r'(?:[\w:]+(?:<[^>]+>)?(?:\s*[&*]+)?)'  # Return type with templates and pointers
                    r'\s+(\w+)\s*\([^)]*\)\s*(?:const|override|final|noexcept)?\s*(?:=\s*0)?\s*(?:->.*?)?\s*\{?$',
                    # Constructor definition with initializer list
                    r'^(\w+)::\1\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{?$',
                ]
                
                closest_function = None
                closest_distance = float('inf')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Check C++ patterns
                    for pattern in cpp_patterns:
                        match = re.match(pattern, line)
                        if match:
                            func_name = match.group(1)
                            current_line = i + 1
                            
                            # If we have a target function, only match that function
                            if target_function:
                                if func_name == target_function:
                                    found_function = {'name': func_name}
                                    function_start = current_line
                                    logger.info(f"Found target function {target_function} manually at line {function_start}")
                                    break
                            # Otherwise find the closest function to our target line
                            else:
                                distance = abs(current_line - line_number)
                                if distance < closest_distance:
                                    closest_distance = distance
                                    closest_function = {'name': func_name}
                                    function_start = current_line
                    
                    if found_function:
                        break
                
                if not found_function and closest_function:
                    found_function = closest_function
                    logger.info(f"Using closest function {found_function.get('name')} at line {function_start}")

            # Create the requirement reference comment
            reference = f"{comment_start}Requirement: {requirement_id}\n"

            # Check if the requirement reference already exists
            if any(requirement_id in line for line in lines):
                # If it exists at the wrong location, move it
                old_locations = [i for i, line in enumerate(lines) if requirement_id in line]
                if old_locations and function_start > 0:
                    logger.info(f"Found existing requirement reference at lines {[l+1 for l in old_locations]}, moving to line {function_start}")
                    # Remove old requirement
                    for old_loc in reversed(old_locations):  # Remove from end to avoid index issues
                        lines.pop(old_loc)
                        # Adjust function_start if we removed lines before it
                        if old_loc < function_start:
                            function_start -= 1
                            logger.debug(f"Adjusted function_start to {function_start} after removing line {old_loc+1}")
                else:
                    logger.debug(f"Requirement {requirement_id} already referenced in {file_path}")
                    return

            # Insert the reference just before the function definition
            if function_start > 0:
                # Find the right spot for the comment (before any existing comments)
                insert_line = function_start
                while insert_line > 1 and any(
                    lines[insert_line-2].strip().startswith(c) 
                    for c in ['#', '//', '/*']
                ):
                    insert_line -= 1
                    logger.debug(f"Moving insert point up to line {insert_line} due to existing comment")
                logger.info(f"Inserting requirement reference at line {insert_line}")
                lines.insert(insert_line - 1, reference)
            else:
                logger.warning(f"No suitable function found, keeping requirement at original location")
                return

            # Write back to file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            # Add to mappings
            if found_function:
                # Handle both FunctionInfo objects and dictionaries
                if isinstance(found_function, dict):
                    func_name = found_function.get('name', '')
                else:
                    func_name = getattr(found_function, 'name', '')
                    
                code_ref = CodeReference(
                    file=str(file_path),
                    line=function_start,
                    function=func_name,
                    type="implementation"
                )
                self.add_mapping(requirement_id, code_ref)
                logger.info(f"Added requirement reference to {file_path} at line {function_start} (function: {func_name})")

        except Exception as e:
            logger.error(f"Error adding requirement reference to {file_path}: {e}")
            logger.error(traceback.format_exc())

    def get_requirements_for_file(self, file_path: str) -> List[str]:
        """Get all requirements that reference a specific file."""
        requirements = []
        for req_id, refs in self.mappings.items():
            for ref in refs:
                if ref.file == file_path:
                    requirements.append(req_id)
                    break  # Found a reference, no need to check other refs for this requirement
        return requirements