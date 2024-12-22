from pathlib import Path
from typing import Dict, List, Optional, AsyncIterator
import os
import fnmatch
import asyncio
from dataclasses import dataclass, field
import yaml
import logging
import traceback
from .ai_integration import OpenAIService
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisProgress:
    """Represents the progress of code analysis."""
    total_files: int
    analyzed_files: int
    current_file: Optional[str] = None
    status: str = "idle"  # idle, running, completed, error
    error_message: Optional[str] = None

@dataclass
class FunctionInfo:
    """Information about a function or method in the code."""
    name: str
    line_number: int
    description: str
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None

@dataclass
class FileAnalysis:
    """Represents the analysis of a single source file."""
    file_path: str
    language: str
    purpose: str
    key_functionality: List[str]
    dependencies: List[str]
    interfaces: List[str]
    implementation_details: List[str]
    potential_issues: List[str]
    domain: Optional[str] = None
    functions: List[FunctionInfo] = field(default_factory=list)

class CodeAnalyzerService:
    """Service for analyzing source code files."""
    
    def __init__(self, workspace_dir: str = "/work", settings_file: str = "plm_settings.yaml"):
        logger.info(f"Initializing CodeAnalyzerService with workspace_dir={workspace_dir}, settings_file={settings_file}")
        self.workspace_dir = Path(workspace_dir)
        self.settings_path = self.workspace_dir / settings_file
        self.cache_dir = self.workspace_dir / ".plm" / "analysis_cache"
        logger.debug(f"Cache directory: {self.cache_dir}")
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Settings path: {self.settings_path}")
        self.settings = self._load_settings()
        logger.debug(f"Loaded settings: {self.settings}")
        
        # Initialize OpenAI service with API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key found in environment variables")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.ai_service = OpenAIService(api_key)
        
        # Initialize analysis state
        self._init_analysis_state()
        self._analysis_task = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # Try to load cached results
        self._load_cached_results()
        
    def _init_analysis_state(self):
        """Initialize or reset the analysis state."""
        self.analysis_state = {
            "status": "not_started",
            "total_files": 0,
            "completed_files": 0,
            "current_file": None,
            "files_to_analyze": [],
            "results": {},
            "message": "Analysis not started"
        }
        logger.debug("Analysis state initialized")
        
    def _load_settings(self) -> dict:
        """Load PLM settings from yaml file."""
        try:
            logger.debug(f"Attempting to load settings from {self.settings_path}")
            if not self.settings_path.exists():
                logger.warning(f"Settings file not found at {self.settings_path}, using default settings")
                default_settings = {
                    'source_folder': 'src',
                    'source_include_patterns': [
                        '**/*.py', '**/*.js', '**/*.ts',  # Web languages
                        '**/*.cpp', '**/*.hpp', '**/*.h', '**/*.c',  # C/C++
                        '**/*.cc', '**/*.cxx', '**/*.hxx', '**/*.inl'  # Additional C++ extensions
                    ],
                    'source_exclude_patterns': [
                        '**/node_modules/**', '**/__pycache__/**', '**/venv/**',
                        '**/build/**', '**/dist/**', '**/CMakeFiles/**',
                        '**/.git/**', '**/.vs/**', '**/.idea/**'
                    ]
                }
                logger.debug(f"Default settings: {default_settings}")
                return default_settings
                
            with open(self.settings_path) as f:
                settings = yaml.safe_load(f)
                logger.debug(f"Successfully loaded settings from file: {settings}")
                
                # Ensure required settings exist with comprehensive defaults
                if 'source_include_patterns' not in settings:
                    settings['source_include_patterns'] = [
                        '**/*.py', '**/*.js', '**/*.ts',  # Web languages
                        '**/*.cpp', '**/*.hpp', '**/*.h', '**/*.c',  # C/C++
                        '**/*.cc', '**/*.cxx', '**/*.hxx', '**/*.inl'  # Additional C++ extensions
                    ]
                    logger.debug("Added default source_include_patterns")
                if 'source_exclude_patterns' not in settings:
                    settings['source_exclude_patterns'] = [
                        '**/node_modules/**', '**/__pycache__/**', '**/venv/**',
                        '**/build/**', '**/dist/**', '**/CMakeFiles/**',
                        '**/.git/**', '**/.vs/**', '**/.idea/**'
                    ]
                    logger.debug("Added default source_exclude_patterns")
                if 'source_folder' not in settings:
                    settings['source_folder'] = 'src'
                    logger.debug("Added default source_folder")
                    
                return settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return default settings on error
            default_settings = {
                'source_folder': 'src',
                'source_include_patterns': [
                    '**/*.py', '**/*.js', '**/*.ts',  # Web languages
                    '**/*.cpp', '**/*.hpp', '**/*.h', '**/*.c',  # C/C++
                    '**/*.cc', '**/*.cxx', '**/*.hxx', '**/*.inl'  # Additional C++ extensions
                ],
                'source_exclude_patterns': [
                    '**/node_modules/**', '**/__pycache__/**', '**/venv/**',
                    '**/build/**', '**/dist/**', '**/CMakeFiles/**',
                    '**/.git/**', '**/.vs/**', '**/.idea/**'
                ]
            }
            logger.debug(f"Using default settings due to error: {default_settings}")
            return default_settings
            
    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included based on patterns."""
        try:
            rel_path = str(Path(file_path).relative_to(self.workspace_dir))
            logger.debug(f"Checking file inclusion: {rel_path}")
            
            # Check exclude patterns first
            for pattern in self.settings.get('source_exclude_patterns', []):
                if fnmatch.fnmatch(rel_path, pattern):
                    logger.debug(f"File {rel_path} excluded by pattern: {pattern}")
                    return False
            
            # Then check include patterns
            include_patterns = self.settings.get('source_include_patterns', [])
            logger.debug(f"Checking against include patterns: {include_patterns}")
            
            for pattern in include_patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    logger.debug(f"File {rel_path} included by pattern: {pattern}")
                    return True
            
            logger.debug(f"File {rel_path} not matched by any include patterns: {include_patterns}")
            return False
        except Exception as e:
            logger.error(f"Error in _should_include_file for {file_path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _get_file_language(self, file_path: str) -> str:
        """Determine the programming language of a file."""
        ext = Path(file_path).suffix.lower()
        logger.debug(f"Determining language for extension: {ext}")
        ext_to_lang = {
            # Web languages
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            
            # C/C++
            '.cpp': 'c++',
            '.hpp': 'c++',
            '.cc': 'c++',
            '.cxx': 'c++',
            '.hxx': 'c++',
            '.h': 'c++',  # Assuming C++ by default, could be C
            '.c': 'c',
            '.inl': 'c++',
            
            # Other languages
            '.java': 'java',
            '.cs': 'c#',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        lang = ext_to_lang.get(ext, 'unknown')
        logger.debug(f"Detected language: {lang} for file extension: {ext}")
        return lang
        
    def _determine_domain(self, file_path: str, content: str) -> Optional[str]:
        """Determine the domain of a file based on its path and content."""
        try:
            rel_path = str(Path(file_path).relative_to(self.workspace_dir))
            logger.debug(f"Determining domain for file: {rel_path}")
            
            # First check if there are configured domains in settings
            domains = self.settings.get('domains', {})
            
            if domains:
                # If domains are configured, use those mappings
                for domain_id, domain_info in domains.items():
                    if domain_id.lower() in rel_path.lower():
                        logger.debug(f"Matched configured domain {domain_id} for file {rel_path}")
                        return domain_id
            else:
                # If no domains are configured, use folder structure
                # Get the first subdirectory after src/ as the domain
                parts = Path(rel_path).parts
                if len(parts) > 1 and parts[0] == 'src':
                    domain = parts[1]  # Use the first subdirectory after src/ as domain
                    logger.debug(f"Using folder structure domain {domain} for file {rel_path}")
                    return domain
            
            logger.debug(f"No domain matched for file {rel_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error determining domain for {file_path}: {e}")
            logger.error(traceback.format_exc())
            return None

    async def analyze_file(self, file_path: str) -> Optional[FileAnalysis]:
        """Analyze a single source code file."""
        try:
            logger.info(f"Starting analysis of file: {file_path}")
            
            if not self._should_include_file(file_path):
                logger.debug(f"Skipping excluded file: {file_path}")
                return None
            
            # Update progress
            self.analysis_state["current_file"] = str(Path(file_path).relative_to(self.workspace_dir))
            
            logger.debug(f"Reading file content: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Successfully read {len(content)} bytes from {file_path}")
                
            language = self._get_file_language(file_path)
            if language == 'unknown':
                logger.debug(f"Skipping file with unknown language: {file_path}")
                return None

            # First analyze the overall file
            file_prompt = f"""Analyze this {language} source code and return a JSON object with the following structure:
{{
    "purpose": "A 1-2 sentence description of the primary purpose",
    "key_functionality": ["List of key features and capabilities"],
    "dependencies": ["List of dependencies and external libraries used"],
    "implementation_details": ["List of important implementation details"],
    "potential_issues": ["List of potential issues or technical debt"]
}}

Source code:
```{language}
{content}
```"""

            logger.debug(f"Sending file analysis request to OpenAI for {file_path}")
            file_response = await self.ai_service.analyze_code(file_prompt, is_function_analysis=False)
            
            # Parse the file analysis response with better error handling
            try:
                # Clean the response
                cleaned_response = self._clean_json_response(file_response)
                logger.debug(f"Cleaned file analysis response: {cleaned_response[:200]}...")
                
                analysis_data = json.loads(cleaned_response)
                
                # Validate required fields
                required_fields = ["purpose", "key_functionality", "dependencies", 
                                 "implementation_details", "potential_issues"]
                missing_fields = [field for field in required_fields if field not in analysis_data]
                if missing_fields:
                    logger.warning(f"Missing required fields in file analysis: {missing_fields}")
                    analysis_data.update({field: [] if field != "purpose" else "Unknown purpose" 
                                       for field in missing_fields})
                
                purpose = analysis_data.get("purpose", "Unknown purpose")
                key_functionality = analysis_data.get("key_functionality", [])
                dependencies = analysis_data.get("dependencies", [])
                implementation_details = analysis_data.get("implementation_details", [])
                potential_issues = analysis_data.get("potential_issues", [])
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing file analysis JSON for {file_path}: {e}")
                logger.error(f"Raw response: {file_response}")
                # Use default values on error
                purpose = "Error analyzing file"
                key_functionality = []
                dependencies = []
                implementation_details = ["Error during analysis"]
                potential_issues = ["Failed to parse analysis results"]
            
            # Now analyze functions specifically
            function_prompt = f"""Analyze the functions/methods in this {language} code and return a JSON array of function objects.
Each function object should have this structure:
{{
    "name": "function name without any formatting",
    "line": line number where function starts (integer),
    "description": "brief description of what the function does",
    "parameters": ["list", "of", "parameter", "names"],
    "return_type": "function return type or null if none"
}}

Source code:
```{language}
{content}
```"""

            logger.debug(f"Sending function analysis request to OpenAI for {file_path}")
            function_response = await self.ai_service.analyze_code(function_prompt, is_function_analysis=True)
            
            # Parse the function analysis response with better error handling
            functions = []
            try:
                # Clean the response
                cleaned_response = self._clean_json_response(function_response)
                logger.debug(f"Cleaned function analysis response: {cleaned_response[:200]}...")
                
                functions_data = json.loads(cleaned_response)
                
                if not isinstance(functions_data, list):
                    logger.error(f"Invalid function analysis response format for {file_path}: not a list")
                    functions_data = []
                
                functions = []
                for func in functions_data:
                    try:
                        # Validate each function object
                        if not isinstance(func, dict):
                            continue
                        
                        name = func.get("name", "").strip()
                        if not name:
                            continue
                            
                        # Remove any markdown formatting from name
                        name = name.replace('*', '').replace('_', '').strip()
                        if name.startswith('Function Name:'):
                            name = name.replace('Function Name:', '').strip()
                            
                        line = func.get("line", 0)
                        if not isinstance(line, int) or line < 0:
                            line = 0
                            
                        description = func.get("description", "").strip()
                        if not description:
                            description = f"Function {name}"
                        # Remove any markdown formatting from description
                        description = description.replace('*', '').replace('_', '').strip()
                        if description.startswith('Function Name:'):
                            description = description.replace('Function Name:', '').strip()
                            
                        parameters = func.get("parameters", [])
                        if not isinstance(parameters, list):
                            parameters = []
                        # Clean parameter names
                        parameters = [p.replace('*', '').replace('_', '').strip() 
                                    for p in parameters if isinstance(p, str)]
                            
                        return_type = func.get("return_type")
                        if return_type and not isinstance(return_type, str):
                            return_type = None
                        elif return_type:
                            # Clean return type
                            return_type = return_type.replace('*', '').replace('_', '').strip()
                            if return_type.startswith('Function Name:'):
                                return_type = None
                        
                        functions.append(FunctionInfo(
                            name=name,
                            line_number=line,
                            description=description,
                            parameters=parameters,
                            return_type=return_type
                        ))
                    except Exception as e:
                        logger.error(f"Error processing function data: {e}")
                        continue
                        
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing function analysis JSON for {file_path}: {e}")
                logger.error(f"Raw response: {function_response}")
            except Exception as e:
                logger.error(f"Error processing function analysis for {file_path}: {e}")
            
            # Determine interfaces and domain
            interfaces = [dep for dep in dependencies if 'interface' in dep.lower()]
            domain = self._determine_domain(file_path, content)
            
            # Create and return the analysis
            analysis = FileAnalysis(
                file_path=str(Path(file_path).relative_to(self.workspace_dir)),
                language=language,
                purpose=purpose,
                key_functionality=key_functionality,
                dependencies=dependencies,
                interfaces=interfaces,
                implementation_details=implementation_details,
                potential_issues=potential_issues,
                domain=domain,
                functions=functions
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.analysis_state['status'] = 'error'
            self.analysis_state['message'] = str(e)
            return None

    def _clean_json_response(self, response: str) -> str:
        """Clean and validate a JSON response from OpenAI."""
        try:
            # Remove markdown code block markers
            cleaned = response.strip()
            if cleaned.startswith('```'):
                first_newline = cleaned.find('\n')
                if first_newline != -1:
                    cleaned = cleaned[first_newline:].strip()
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].strip()
            
            # Remove any trailing closing braces that would make the JSON invalid
            while cleaned.count('[') < cleaned.count(']'):
                cleaned = cleaned.rstrip(']').strip()
            while cleaned.count('{') < cleaned.count('}'):
                cleaned = cleaned.rstrip('}').strip()
            
            # Add missing closing brackets if needed
            while cleaned.count('[') > cleaned.count(']'):
                cleaned = cleaned.strip() + ']'
            while cleaned.count('{') > cleaned.count('}'):
                cleaned = cleaned.strip() + '}'
            
            # Try to parse it to validate
            json.loads(cleaned)
            
            return cleaned
        except Exception as e:
            logger.error(f"Error cleaning JSON response: {e}")
            logger.error(f"Original response: {response}")
            raise

    async def get_analysis_progress(self) -> AnalysisProgress:
        """Get current analysis progress."""
        return AnalysisProgress(
            total_files=self.analysis_state['total_files'],
            analyzed_files=self.analysis_state['completed_files'],
            current_file=self.analysis_state['current_file'],
            status=self.analysis_state['status'],
            error_message=self.analysis_state['message']
        )

    async def analyze_codebase(self) -> AsyncIterator[Optional[FileAnalysis]]:
        """Analyze all source code files in the workspace."""
        try:
            logger.info("Starting codebase analysis")
            source_dir = self.workspace_dir / self.settings.get('source_folder', 'src')
            logger.debug(f"Source directory: {source_dir}")
            
            # Reset progress
            self.analysis_state['status'] = 'running'
            self.analysis_state['total_files'] = 0
            self.analysis_state['completed_files'] = 0
            self.analysis_state['current_file'] = None
            self.analysis_state['files_to_analyze'] = []
            self.analysis_state['results'] = {}
            self.analysis_state['message'] = None
            
            # First pass to count files
            total_files = 0
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    if self._should_include_file(str(file_path)):
                        total_files += 1
                        self.analysis_state['files_to_analyze'].append(str(file_path))
            
            logger.info(f"Found {total_files} files to analyze")
            self.analysis_state['total_files'] = total_files
            
            # Second pass to analyze files
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    if self._should_include_file(str(file_path)):
                        analysis = await self.analyze_file(str(file_path))
                        yield analysis
            
            # Update final progress
            self.analysis_state['status'] = 'completed'
            self.analysis_state['current_file'] = None
            self.analysis_state['message'] = f"Analysis completed for {total_files} files"
            logger.info("Codebase analysis completed")
                
        except Exception as e:
            logger.error(f"Error during codebase analysis: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.analysis_state['status'] = 'error'
            self.analysis_state['message'] = str(e)
            raise

    def start_analysis_task(self):
        """Start the background analysis task."""
        try:
            if self._analysis_task and not self._analysis_task.done():
                logger.debug("Analysis task already running")
                return
            
            logger.debug("Starting new analysis task")
            loop = asyncio.get_event_loop()
            self._analysis_task = loop.create_task(self._run_analysis())
            
        except Exception as e:
            logger.error(f"Error starting analysis task: {e}", exc_info=True)
            self.analysis_state["status"] = "error"
            self.analysis_state["message"] = f"Failed to start analysis: {str(e)}"
    
    async def _run_analysis(self):
        """Run analysis in background."""
        try:
            logger.debug("Starting background analysis")
            files_to_analyze = self.analysis_state['files_to_analyze']
            
            if not files_to_analyze:
                logger.warning("No files to analyze")
                self.analysis_state['status'] = 'completed'
                self.analysis_state['message'] = "No files to analyze"
                return
            
            self.analysis_state.update({
                'status': 'in_progress',
                'message': f"Analyzing {len(files_to_analyze)} files",
                'total_files': len(files_to_analyze),
                'completed_files': 0
            })
            
            loop = asyncio.get_event_loop()
            
            for file_path in files_to_analyze:
                if self.analysis_state['status'] != 'in_progress':
                    logger.debug("Analysis interrupted")
                    break
                    
                logger.debug(f"Analyzing file: {file_path}")
                self.analysis_state['current_file'] = str(Path(file_path).relative_to(self.workspace_dir))
                
                try:
                    # Run the analysis in a thread pool to avoid blocking the event loop
                    analysis = await loop.run_in_executor(
                        self._executor,
                        self._analyze_file_sync,
                        file_path
                    )
                    
                    # Allow other tasks to run
                    await asyncio.sleep(0)
                    
                    if analysis:
                        rel_path = str(Path(file_path).relative_to(self.workspace_dir))
                        self.analysis_state['results'][rel_path] = analysis.__dict__
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {e}", exc_info=True)
                    continue
                finally:
                    self.analysis_state['completed_files'] += 1
                    completed = self.analysis_state['completed_files']
                    total = self.analysis_state['total_files']
                    logger.debug(f"Completed {completed} of {total} files")
            
            # Save results to cache after completion
            await loop.run_in_executor(self._executor, self._save_analysis_results)
            
            self.analysis_state.update({
                'status': 'completed',
                'current_file': None,
                'message': f"Analysis completed for {len(files_to_analyze)} files"
            })
            logger.info("Analysis task completed successfully")
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            self.analysis_state.update({
                'status': 'error',
                'message': str(e)
            })

    def _analyze_file_sync(self, file_path: str) -> Optional[FileAnalysis]:
        """Synchronous version of analyze_file for running in thread pool."""
        try:
            if not self._should_include_file(file_path):
                logger.debug(f"Skipping excluded file: {file_path}")
                return None
            
            logger.debug(f"Reading file content: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Successfully read {len(content)} bytes from {file_path}")
                
            language = self._get_file_language(file_path)
            if language == 'unknown':
                logger.debug(f"Skipping file with unknown language: {file_path}")
                return None

            # First analyze the overall file
            file_prompt = f"""Analyze this {language} source code and return a JSON object with the following structure:
{{
    "purpose": "A 1-2 sentence description of the primary purpose",
    "key_functionality": ["List of key features and capabilities"],
    "dependencies": ["List of dependencies and external libraries used"],
    "implementation_details": ["List of important implementation details"],
    "potential_issues": ["List of potential issues or technical debt"]
}}

Source code:
```{language}
{content}
```"""

            logger.debug(f"Sending file analysis request to OpenAI for {file_path}")
            file_response = asyncio.run(self.ai_service.analyze_code(file_prompt, is_function_analysis=False))
            
            # Parse the file analysis response with better error handling
            try:
                # Clean the response
                cleaned_response = self._clean_json_response(file_response)
                logger.debug(f"Cleaned file analysis response: {cleaned_response[:200]}...")
                
                analysis_data = json.loads(cleaned_response)
                
                # Validate required fields
                required_fields = ["purpose", "key_functionality", "dependencies", 
                                 "implementation_details", "potential_issues"]
                missing_fields = [field for field in required_fields if field not in analysis_data]
                if missing_fields:
                    logger.warning(f"Missing required fields in file analysis: {missing_fields}")
                    analysis_data.update({field: [] if field != "purpose" else "Unknown purpose" 
                                       for field in missing_fields})
                
                purpose = analysis_data.get("purpose", "Unknown purpose")
                key_functionality = analysis_data.get("key_functionality", [])
                dependencies = analysis_data.get("dependencies", [])
                implementation_details = analysis_data.get("implementation_details", [])
                potential_issues = analysis_data.get("potential_issues", [])
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing file analysis JSON for {file_path}: {e}")
                logger.error(f"Raw response: {file_response}")
                # Use default values on error
                purpose = "Error analyzing file"
                key_functionality = []
                dependencies = []
                implementation_details = ["Error during analysis"]
                potential_issues = ["Failed to parse analysis results"]
            
            # Now analyze functions specifically
            function_prompt = f"""Analyze the functions/methods in this {language} code and return a JSON array of function objects.
Each function object should have this structure:
{{
    "name": "function name without any formatting",
    "line": line number where function starts (integer),
    "description": "brief description of what the function does",
    "parameters": ["list", "of", "parameter", "names"],
    "return_type": "function return type or null if none"
}}

Source code:
```{language}
{content}
```"""

            logger.debug(f"Sending function analysis request to OpenAI for {file_path}")
            function_response = asyncio.run(self.ai_service.analyze_code(function_prompt, is_function_analysis=True))
            
            # Parse the function analysis response with better error handling
            functions = []
            try:
                # Clean the response
                cleaned_response = self._clean_json_response(function_response)
                logger.debug(f"Cleaned function analysis response: {cleaned_response[:200]}...")
                
                functions_data = json.loads(cleaned_response)
                
                if not isinstance(functions_data, list):
                    logger.error(f"Invalid function analysis response format for {file_path}: not a list")
                    functions_data = []
                
                functions = []
                for func in functions_data:
                    try:
                        # Validate each function object
                        if not isinstance(func, dict):
                            continue
                        
                        name = func.get("name", "").strip()
                        if not name:
                            continue
                            
                        # Remove any markdown formatting from name
                        name = name.replace('*', '').replace('_', '').strip()
                        if name.startswith('Function Name:'):
                            name = name.replace('Function Name:', '').strip()
                            
                        line = func.get("line", 0)
                        if not isinstance(line, int) or line < 0:
                            line = 0
                            
                        description = func.get("description", "").strip()
                        if not description:
                            description = f"Function {name}"
                        # Remove any markdown formatting from description
                        description = description.replace('*', '').replace('_', '').strip()
                        if description.startswith('Function Name:'):
                            description = description.replace('Function Name:', '').strip()
                            
                        parameters = func.get("parameters", [])
                        if not isinstance(parameters, list):
                            parameters = []
                        # Clean parameter names
                        parameters = [p.replace('*', '').replace('_', '').strip() 
                                    for p in parameters if isinstance(p, str)]
                            
                        return_type = func.get("return_type")
                        if return_type and not isinstance(return_type, str):
                            return_type = None
                        elif return_type:
                            # Clean return type
                            return_type = return_type.replace('*', '').replace('_', '').strip()
                            if return_type.startswith('Function Name:'):
                                return_type = None
                        
                        functions.append(FunctionInfo(
                            name=name,
                            line_number=line,
                            description=description,
                            parameters=parameters,
                            return_type=return_type
                        ))
                    except Exception as e:
                        logger.error(f"Error processing function data: {e}")
                        continue
                        
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing function analysis JSON for {file_path}: {e}")
                logger.error(f"Raw response: {function_response}")
            except Exception as e:
                logger.error(f"Error processing function analysis for {file_path}: {e}")
            
            # Determine interfaces and domain
            interfaces = [dep for dep in dependencies if 'interface' in dep.lower()]
            domain = self._determine_domain(file_path, content)
            
            # Create and return the analysis
            analysis = FileAnalysis(
                file_path=str(Path(file_path).relative_to(self.workspace_dir)),
                language=language,
                purpose=purpose,
                key_functionality=key_functionality,
                dependencies=dependencies,
                interfaces=interfaces,
                implementation_details=implementation_details,
                potential_issues=potential_issues,
                domain=domain,
                functions=functions
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _save_analysis_results(self):
        """Save analysis results to cache file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cache_file = self.cache_dir / f"analysis_results_{timestamp}.json"
            
            # Convert analysis results to JSON-serializable format
            results_dict = {}
            for file_path, analysis in self.analysis_state['results'].items():
                if isinstance(analysis, dict):
                    # If it's already a dict, convert any FunctionInfo objects in the functions list
                    if 'functions' in analysis:
                        analysis['functions'] = [
                            {
                                'name': f.name,
                                'line_number': f.line_number,
                                'description': f.description,
                                'parameters': f.parameters,
                                'return_type': f.return_type
                            } if isinstance(f, FunctionInfo) else f
                            for f in analysis['functions']
                        ]
                    results_dict[file_path] = analysis
                else:
                    # Convert FileAnalysis object to dict and handle FunctionInfo objects
                    analysis_dict = analysis.__dict__.copy()
                    analysis_dict['functions'] = [
                        {
                            'name': f.name,
                            'line_number': f.line_number,
                            'description': f.description,
                            'parameters': f.parameters,
                            'return_type': f.return_type
                        }
                        for f in analysis.functions
                    ]
                    results_dict[file_path] = analysis_dict
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, indent=2)
            logger.info(f"Saved analysis results to {cache_file}")
            
            # Clean up old cache files (keep last 5)
            cache_files = sorted(self.cache_dir.glob("analysis_results_*.json"))
            for old_file in cache_files[:-5]:
                old_file.unlink()
                logger.debug(f"Removed old cache file: {old_file}")
                
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            logger.error(traceback.format_exc())

    def _load_cached_results(self):
        """Load most recent cached analysis results if available."""
        try:
            cache_files = sorted(self.cache_dir.glob("analysis_results_*.json"))
            if not cache_files:
                logger.debug("No cached analysis results found")
                return
            
            latest_cache = cache_files[-1]
            logger.info(f"Loading cached analysis results from {latest_cache}")
            
            with open(latest_cache, 'r', encoding='utf-8') as f:
                cached_results = json.load(f)
            
            # Convert cached results back to proper objects
            reconstructed_results = {}
            for file_path, analysis in cached_results.items():
                # Reconstruct FunctionInfo objects
                if 'functions' in analysis:
                    analysis['functions'] = [
                        FunctionInfo(
                            name=func['name'],
                            line_number=func['line_number'],
                            description=func['description'],
                            parameters=func['parameters'],
                            return_type=func.get('return_type')
                        )
                        for func in analysis['functions']
                    ]
                reconstructed_results[file_path] = analysis
            
            self.analysis_state['results'] = reconstructed_results
            self.analysis_state['status'] = 'completed'
            self.analysis_state['message'] = f"Loaded {len(reconstructed_results)} files from cache"
            self.analysis_state['total_files'] = len(reconstructed_results)
            self.analysis_state['completed_files'] = len(reconstructed_results)
            
            logger.info(f"Loaded {len(reconstructed_results)} files from cache")
            
        except Exception as e:
            logger.error(f"Error loading cached results: {e}")
            logger.error(traceback.format_exc())