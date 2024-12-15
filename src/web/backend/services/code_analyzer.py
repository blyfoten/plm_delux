from pathlib import Path
from typing import Dict, List, Optional, AsyncIterator
import os
import fnmatch
import asyncio
from dataclasses import dataclass
import yaml
import logging
import traceback
from .ai_integration import OpenAIService

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

class CodeAnalyzerService:
    """Service for analyzing source code files."""
    
    def __init__(self, workspace_dir: str = "/work", settings_file: str = "plm_settings.yaml"):
        logger.info(f"Initializing CodeAnalyzerService with workspace_dir={workspace_dir}, settings_file={settings_file}")
        self.workspace_dir = Path(workspace_dir)
        self.settings_path = self.workspace_dir / settings_file
        logger.debug(f"Settings path: {self.settings_path}")
        self.settings = self._load_settings()
        logger.debug(f"Loaded settings: {self.settings}")
        
        # Initialize OpenAI service with API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key found in environment variables")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.ai_service = OpenAIService(api_key)
        
        self._progress = AnalysisProgress(total_files=0, analyzed_files=0, status="idle")
        self._analysis_lock = asyncio.Lock()
        
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
            
            # Check path-based domain matching
            domains = self.settings.get('domains', {})
            logger.debug(f"Available domains: {list(domains.keys())}")
            
            for domain_id, domain_info in domains.items():
                if domain_id.lower() in rel_path.lower():
                    logger.debug(f"Matched domain {domain_id} for file {rel_path}")
                    return domain_id
            
            logger.debug(f"No domain matched for file {rel_path}")
            return None
        except Exception as e:
            logger.error(f"Error determining domain for {file_path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def analyze_file(self, file_path: str) -> Optional[FileAnalysis]:
        """Analyze a single source code file."""
        try:
            logger.info(f"Starting analysis of file: {file_path}")
            
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
                
            # Update progress
            async with self._analysis_lock:
                self._progress.current_file = file_path
                self._progress.status = "running"
                logger.debug(f"Updated progress - current file: {file_path}, status: {self._progress.status}")
            
            # Prepare prompt for OpenAI
            prompt = f"""Analyze this {language} source code and provide:
1. Primary purpose (1-2 sentences)
2. Key functionality (bullet points)
3. Dependencies and interfaces
4. Important implementation details
5. Any potential issues or technical debt

Source code:
```{language}
{content}
```"""
            
            logger.debug(f"Sending analysis request to OpenAI for {file_path}")
            response = await self.ai_service.analyze_code(prompt)
            logger.debug(f"Received response from OpenAI: {response[:200]}...")
            
            # Parse the response into structured data
            try:
                # Split response into sections
                sections = response.split('\n\n')
                
                # Extract purpose (first section)
                purpose = sections[0].strip() if sections else "Unknown purpose"
                
                # Extract key functionality (second section)
                key_functionality = []
                if len(sections) > 1:
                    for line in sections[1].split('\n'):
                        if line.strip().startswith('-'):
                            key_functionality.append(line.strip()[1:].strip())
                
                # Extract dependencies (third section)
                dependencies = []
                if len(sections) > 2:
                    for line in sections[2].split('\n'):
                        if line.strip().startswith('-'):
                            dependencies.append(line.strip()[1:].strip())
                
                # Extract implementation details (fourth section)
                implementation_details = []
                if len(sections) > 3:
                    for line in sections[3].split('\n'):
                        if line.strip().startswith('-'):
                            implementation_details.append(line.strip()[1:].strip())
                
                # Extract potential issues (fifth section)
                potential_issues = []
                if len(sections) > 4:
                    for line in sections[4].split('\n'):
                        if line.strip().startswith('-'):
                            potential_issues.append(line.strip()[1:].strip())
                
                # Determine interfaces from dependencies and implementation details
                interfaces = [dep for dep in dependencies if 'interface' in dep.lower()]
                
                # Determine domain
                domain = self._determine_domain(file_path, content)
                
                analysis = FileAnalysis(
                    file_path=str(Path(file_path).relative_to(self.workspace_dir)),
                    language=language,
                    purpose=purpose,
                    key_functionality=key_functionality,
                    dependencies=dependencies,
                    interfaces=interfaces,
                    implementation_details=implementation_details,
                    potential_issues=potential_issues,
                    domain=domain
                )
                
                # Update progress
                async with self._analysis_lock:
                    self._progress.analyzed_files += 1
                    logger.debug(f"Updated progress - analyzed files: {self._progress.analyzed_files}")
                
                return analysis
                
            except Exception as e:
                logger.error(f"Error parsing OpenAI response for {file_path}: {e}")
                logger.error(f"Raw response: {response}")
                raise
                
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            async with self._analysis_lock:
                self._progress.status = "error"
                self._progress.error_message = str(e)
            return None

    async def get_analysis_progress(self) -> AnalysisProgress:
        """Get current analysis progress."""
        async with self._analysis_lock:
            return self._progress

    async def analyze_codebase(self) -> AsyncIterator[Optional[FileAnalysis]]:
        """Analyze all source code files in the workspace."""
        try:
            logger.info("Starting codebase analysis")
            source_dir = self.workspace_dir / self.settings.get('source_folder', 'src')
            logger.debug(f"Source directory: {source_dir}")
            
            # Reset progress
            async with self._analysis_lock:
                self._progress = AnalysisProgress(total_files=0, analyzed_files=0, status="running")
            
            # First pass to count files
            total_files = 0
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    if self._should_include_file(str(file_path)):
                        total_files += 1
            
            logger.info(f"Found {total_files} files to analyze")
            async with self._analysis_lock:
                self._progress.total_files = total_files
            
            # Second pass to analyze files
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    if self._should_include_file(str(file_path)):
                        analysis = await self.analyze_file(str(file_path))
                        yield analysis
            
            # Update final progress
            async with self._analysis_lock:
                self._progress.status = "completed"
                self._progress.current_file = None
                logger.info("Codebase analysis completed")
                
        except Exception as e:
            logger.error(f"Error during codebase analysis: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            async with self._analysis_lock:
                self._progress.status = "error"
                self._progress.error_message = str(e)
            raise