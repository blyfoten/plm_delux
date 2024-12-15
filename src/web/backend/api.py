"""FastAPI backend for the PLM web interface."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import os
import frontmatter
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime
import json
import traceback
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('plm_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

# Import services
from .services import CodeAnalyzerService, FileAnalysis, AnalysisProgress, OpenAIService, MockAIService, GeneratedRequirement
from .services.requirements_parser import RequirementsParser, Requirement
from .services.architecture import Block, system_architecture, save_architecture
from .services.visualizer import ArchitectureVisualizer
from .services.requirements_mapper import RequirementsMapper, CodeReference

# Get workspace directory from environment or use default
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/work")

# Add after other global variables
ANALYSIS_CACHE_DIR = Path(WORKSPACE_DIR) / ".plm" / "analysis_cache"
ANALYSIS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def save_analysis_results():
    """Save current analysis results to disk."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache_file = ANALYSIS_CACHE_DIR / f"analysis_results_{timestamp}.json"
    
    # Convert analysis results to serializable format
    serializable_results = {
        file_path: {
            "file_path": analysis.file_path,
            "language": analysis.language,
            "purpose": analysis.purpose,
            "key_functionality": analysis.key_functionality,
            "dependencies": analysis.dependencies,
            "interfaces": analysis.interfaces,
            "implementation_details": analysis.implementation_details,
            "potential_issues": analysis.potential_issues,
            "domain": analysis.domain
        }
        for file_path, analysis in analysis_results.items()
    }
    
    with open(cache_file, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    logger.info(f"Saved analysis results to {cache_file}")
    return cache_file

def load_latest_analysis():
    """Load the most recent analysis results from disk."""
    try:
        cache_files = sorted(ANALYSIS_CACHE_DIR.glob("analysis_results_*.json"))
        if not cache_files:
            return None
            
        latest_file = cache_files[-1]
        with open(latest_file) as f:
            data = json.load(f)
            
        # Convert back to FileAnalysis objects
        return {
            file_path: FileAnalysis(**analysis_data)
            for file_path, analysis_data in data.items()
        }
    except Exception as e:
        logger.error(f"Error loading analysis cache: {e}")
        return None

# Pydantic models for API
class CodeReferenceModel(BaseModel):
    """Model for code references."""
    file: str
    line: int
    function: str
    type: str
    url: str

class RequirementBase(BaseModel):
    """Base model for requirements."""
    id: str
    domain: str
    description: str
    linked_blocks: List[str]
    additional_notes: List[str]
    content: str
    code_references: List[CodeReferenceModel] = []

    class Config:
        """Pydantic config."""
        from_attributes = True

class ArchitectureBlock(BaseModel):
    """Architecture block data model."""
    block_id: str
    name: str
    requirements: List[str] = []
    subblocks: List[str] = []
    x: float = 0
    y: float = 0

class ArchitectureUpdateRequest(BaseModel):
    """Request model for architecture updates."""
    blocks: Dict[str, ArchitectureBlock]

class CodeGenerationRequest(BaseModel):
    """Request model for code generation."""
    requirement_id: str

class CodeGenerationResponse(BaseModel):
    """Response model for code generation."""
    message: str
    files: List[str]

class ArchitectureResponse(BaseModel):
    """Response model for architecture endpoint."""
    root_id: str
    blocks: Dict[str, ArchitectureBlock]

class DomainConfig(BaseModel):
    """Configuration for a domain."""
    name: str
    description: str = ""
    parent_domain: Optional[str] = None
    subdomain_ids: List[str] = []

    def model_dump(self, *args, **kwargs):
        """Override model_dump to ensure proper serialization."""
        data = super().model_dump(*args, **kwargs)
        # Ensure subdomain_ids is always a list
        data['subdomain_ids'] = data.get('subdomain_ids', [])
        return data

class PLMSettings(BaseModel):
    """Settings model for PLM."""
    source_folder: str = "src"  # Used for both input (code analysis) and output (generated code)
    requirements_folder: str = "requirements"
    architecture_folder: str = "architecture"
    folder_structure: str = "hierarchical"  # or "flat"
    preferred_languages: List[str] = ["python", "javascript"]
    custom_llm_instructions: str = ""
    source_include_patterns: List[str] = ["**/*.py", "**/*.js", "**/*.ts"]
    source_exclude_patterns: List[str] = ["**/node_modules/**", "**/__pycache__/**", "**/venv/**"]
    domains: Dict[str, DomainConfig] = {
        "ui": DomainConfig(
            name="User Interface",
            description="User interface components and interactions",
            subdomain_ids=[]
        ),
        "motor_and_doors": DomainConfig(
            name="Motor and Doors",
            description="Motor control and door management systems",
            subdomain_ids=[]
        ),
        "offboard": DomainConfig(
            name="Offboard Systems",
            description="External and cloud-based systems",
            subdomain_ids=[]
        )
    }

    class Config:
        """Pydantic config."""
        from_attributes = True
        populate_by_name = True

    @classmethod
    def get_default_settings(cls) -> "PLMSettings":
        """Get default settings."""
        return cls()

    def model_dump(self, *args, **kwargs):
        """Override model_dump to ensure proper serialization."""
        data = super().model_dump(*args, **kwargs)
        # Ensure domains are properly serialized with empty lists
        data['domains'] = {
            domain_id: {
                'name': domain.name,
                'description': domain.description,
                'parent_domain': domain.parent_domain,
                'subdomain_ids': domain.subdomain_ids or []  # Ensure empty list instead of None
            }
            for domain_id, domain in self.domains.items()
        }
        return data

def load_settings() -> PLMSettings:
    """Load settings from file or create default."""
    settings_path = Path(WORKSPACE_DIR) / "plm_settings.yaml"
    if settings_path.exists():
        with open(settings_path, "r") as f:
            return PLMSettings(**yaml.safe_load(f))
    return PLMSettings.get_default_settings()

def save_settings(settings: PLMSettings):
    """Save settings to YAML file with comments."""
    settings_path = Path(WORKSPACE_DIR) / "plm_settings.yaml"
    
    # Create settings dict with comments
    settings_dict = settings.model_dump()
    
    # Add comments to the YAML output
    yaml_str = """# PLM Settings Configuration
# Folder paths relative to workspace
source_folder: {source_folder}  # Used for both input (code analysis) and output (generated code)
requirements_folder: {requirements_folder}
architecture_folder: {architecture_folder}

# Folder structure preference (hierarchical or flat)
folder_structure: {folder_structure}

# Preferred programming languages for code generation
preferred_languages:
{languages}

# Custom instructions for LLM interactions
custom_llm_instructions: "{custom_llm_instructions}"

# Source code scanning patterns
source_include_patterns:
{includes}

# Patterns to exclude from source scanning
source_exclude_patterns:
{excludes}

# Domain configurations
domains:
{domains}""".format(
        source_folder=settings_dict["source_folder"],
        requirements_folder=settings_dict["requirements_folder"],
        architecture_folder=settings_dict["architecture_folder"],
        folder_structure=settings_dict["folder_structure"],
        languages="\n".join(f"  - {lang}" for lang in settings_dict["preferred_languages"]),
        custom_llm_instructions=settings_dict["custom_llm_instructions"],
        includes="\n".join(f'  - "{pattern}"' for pattern in settings_dict["source_include_patterns"]),
        excludes="\n".join(f'  - "{pattern}"' for pattern in settings_dict["source_exclude_patterns"]),
        domains="\n".join(
            f"  {domain_id}:\n" +
            f"    name: {domain_data['name']}\n" +
            f"    description: {domain_data['description']}\n" +
            (f"    parent_domain: {domain_data['parent_domain']}\n" if domain_data.get('parent_domain') else "") +
            f"    subdomain_ids: {domain_data.get('subdomain_ids', [])}"
            for domain_id, domain_data in settings_dict["domains"].items()
        )
    )
    
    with open(settings_path, "w") as f:
        f.write(yaml_str)

# Initialize components with settings
settings = load_settings()
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/work")

parser = RequirementsParser(WORKSPACE_DIR)
mapper = RequirementsMapper(WORKSPACE_DIR)

# Use MockAIService if no API key is available
api_key = os.getenv("OPENAI_API_KEY")
ai = OpenAIService(api_key) if api_key else MockAIService()

visualizer = ArchitectureVisualizer(parser.parse_all())

# Initialize services
code_analyzer = CodeAnalyzerService(WORKSPACE_DIR)
analysis_results: Dict[str, FileAnalysis] = {}

def convert_architecture_to_dict(block: Block) -> dict:
    """Convert architecture block to dictionary for API response."""
    blocks = {}
    
    def process_block(b: Block):
        blocks[b.block_id] = {
            "block_id": b.block_id,
            "name": b.name,
            "requirements": b.requirements,
            "subblocks": [sb.block_id for sb in b.subblocks],
            "x": getattr(b, 'x', 0),
            "y": getattr(b, 'y', 0)
        }
        for subblock in b.subblocks:
            process_block(subblock)
    
    process_block(block)
    
    return {
        "root_id": block.block_id,
        "blocks": blocks
    }

app = FastAPI(title="PLM Web Interface")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/requirements")
async def get_requirements():
    """Get all requirements with their code references."""
    logger.info("Fetching requirements")
    try:
        requirements = parser.parse_all()
        logger.debug(f"Raw requirements: {requirements}")
        
        # Scan code for requirement references
        mapper.scan_code_for_references()
        
        # Convert requirements to a dictionary format the frontend expects
        response = {}
        for req_id, req in requirements.items():
            code_refs = mapper.get_references(req_id)
            logger.info(f"Found {len(code_refs)} code references for {req_id}")
            
            code_ref_models = []
            for ref in code_refs:
                url = mapper.get_vscode_url(ref)
                logger.info(f"Generated URL for {req_id}: {url}")
                code_ref_models.append({
                    "file": ref.file,
                    "line": ref.line,
                    "function": ref.function,
                    "type": ref.type,
                    "url": url
                })
            
            response[req_id] = {
                "id": req.id,
                "domain": req.domain,
                "description": req.description,
                "linked_blocks": req.linked_blocks,
                "additional_notes": req.additional_notes,
                "content": req.content,
                "code_references": code_ref_models
            }
        
        logger.debug(f"Sending response: {response}")
        return {"requirements": response}
    except Exception as e:
        logger.error(f"Error fetching requirements: {str(e)}")
        logger.exception("Detailed traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/architecture", response_model=ArchitectureResponse)
async def get_architecture():
    """Get system architecture."""
    logger.info("Fetching architecture")
    try:
        arch_dict = convert_architecture_to_dict(system_architecture)
        return ArchitectureResponse(**arch_dict)
    except Exception as e:
        logger.error(f"Error fetching architecture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/architecture")
async def update_architecture(request: ArchitectureUpdateRequest):
    """Update the architecture based on visual editor changes."""
    logger.info("Updating architecture")
    try:
        # Update the architecture
        for block_id, block_data in request.blocks.items():
            # Update block properties
            if block_id in system_architecture.blocks:
                block = system_architecture.blocks[block_id]
                block.name = block_data.name
                block.requirements = block_data.requirements
                block.x = block_data.x
                block.y = block_data.y
        
        # Save the updated architecture
        save_architecture(system_architecture, WORKSPACE_DIR)
        
        # Regenerate visualization
        requirements = parser.parse_all()
        visualizer = ArchitectureVisualizer(requirements)
        visualizer.generate_diagram(system_architecture, str(Path(WORKSPACE_DIR) / "architecture" / "diagram"))
        
        return {"message": "Architecture updated successfully"}
    except Exception as e:
        logger.error(f"Error updating architecture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/code/generate", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code for a requirement."""
    logger.info(f"Generating code for requirement: {request.requirement_id}")
    
    try:
        requirements = parser.parse_all()
        logger.debug(f"All requirements: {list(requirements.keys())}")
        
        if request.requirement_id not in requirements:
            logger.error(f"Requirement not found: {request.requirement_id}")
            raise HTTPException(status_code=404, detail=f"Requirement {request.requirement_id} not found")
        
        requirement = requirements[request.requirement_id]
        logger.info(f"Found requirement: {requirement.description}")
        logger.debug(f"Requirement object type: {type(requirement)}")
        logger.debug(f"Requirement attributes: {vars(requirement)}")
        
        # Convert Requirement to Pydantic model
        requirement_model = RequirementBase(
            id=requirement.id,
            domain=requirement.domain,
            description=requirement.description,
            linked_blocks=requirement.linked_blocks,
            additional_notes=requirement.additional_notes,
            content=requirement.content
        )
        logger.debug(f"Created Pydantic model: {requirement_model.model_dump()}")
        
        # Convert to dict for AI service
        requirement_dict = requirement_model.model_dump()
        logger.debug(f"Converted to dict for AI service: {requirement_dict}")
        
        # Load current settings
        current_settings = load_settings()
        
        # Log the exact structure being passed to generate_code
        logger.info(f"Calling ai.generate_code with dict: {requirement_dict}")
        generated = await ai.generate_code(requirement_dict)
        logger.info(f"Generated code for block: {generated.block_id}")
        
        # Add tests
        generated = await ai.enhance_code_with_tests(generated)
        logger.info("Added tests to generated code")
        
        # Save the generated code to the source folder
        output_dir = Path(WORKSPACE_DIR) / current_settings.source_folder / generated.block_id.lower()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        impl_file = output_dir / "implementation.py"
        with open(impl_file, "w") as f:
            f.write(generated.code)
        logger.info(f"Saved generated code to: {impl_file}")
        
        if generated.tests:
            test_file = output_dir / "test_implementation.py"
            with open(test_file, "w") as f:
                f.write(generated.tests)
            logger.info(f"Saved tests to: {test_file}")
        
        # Update requirement mappings
        mapper.scan_code_for_references()
        
        return CodeGenerationResponse(
            message="Code generated successfully",
            files=[str(impl_file)]
        )
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        logger.exception("Detailed traceback:")
        raise HTTPException(status_code=500, detail=str(e)) 

@app.get("/api/settings")
async def get_settings():
    """Get current PLM settings."""
    logger.info("Fetching settings")
    try:
        settings = load_settings()
        # Convert to dict and return as JSONResponse
        return JSONResponse(
            content=jsonable_encoder(settings.model_dump()),
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        logger.exception("Detailed traceback:")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
            headers={"Content-Type": "application/json"}
        )

@app.put("/api/settings")
async def update_settings(new_settings: PLMSettings):
    """Update PLM settings."""
    logger.info("Updating settings")
    try:
        logger.debug(f"Received settings data: {new_settings.model_dump()}")
        logger.debug(f"Domains data: {new_settings.domains}")
        save_settings(new_settings)
        return JSONResponse(
            content={"message": "Settings updated successfully"},
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        logger.error(f"Settings data that caused error: {vars(new_settings)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
            headers={"Content-Type": "application/json"}
        )

class FileAnalysisModel(BaseModel):
    """API model for file analysis results."""
    file_path: str
    language: str
    purpose: str
    key_functionality: List[str]
    dependencies: List[str]
    interfaces: List[str]
    implementation_details: List[str]
    potential_issues: List[str]
    domain: Optional[str] = None

class AnalysisProgressModel(BaseModel):
    """API model for analysis progress."""
    total_files: int
    analyzed_files: int
    current_file: Optional[str] = None
    status: str
    error_message: Optional[str] = None

class GenerateRequirementsRequest(BaseModel):
    """Request model for requirements generation."""
    domain: str

class AnalyzeRequest(BaseModel):
    """Request model for code analysis."""
    files: Optional[List[str]] = None  # If None, analyze all files

@app.post("/api/analyze/start")
async def start_analysis(request: AnalyzeRequest):
    """Start analyzing the codebase."""
    logger.info("=== START ANALYSIS ENDPOINT CALLED ===")
    logger.debug(f"Request: {request}")
    logger.debug(f"Workspace dir: {WORKSPACE_DIR}")
    logger.debug(f"Current settings: {load_settings()}")
    
    try:
        logger.info("Starting code analysis")
        analysis_results.clear()
        
        # If specific files are provided, only analyze those
        if request.files:
            logger.info(f"Starting analysis of {len(request.files)} selected files")
            for file_path in request.files:
                full_path = os.path.join(WORKSPACE_DIR, file_path)
                logger.debug(f"Analyzing file: {full_path}")
                analysis = await code_analyzer.analyze_file(full_path)
                if analysis:
                    analysis_results[analysis.file_path] = analysis
                    logger.debug(f"Analysis completed for {full_path}")
            
            # Save results for specific file analysis
            cache_file = save_analysis_results()
            logger.info(f"Analysis results saved to {cache_file}")
            response_data = {
                "message": "Analysis completed successfully",
                "status": "completed",
                "cache_file": str(cache_file),
                "files_analyzed": len(analysis_results)
            }
            return JSONResponse(content=jsonable_encoder(response_data))
        else:
            # Analyze all files
            logger.info("Starting analysis of entire codebase")
            
            # Create a background task for the analysis
            async def run_analysis():
                try:
                    logger.info("Background analysis task started")
                    async for analysis in code_analyzer.analyze_codebase():
                        if analysis:
                            logger.debug(f"Received analysis for {analysis.file_path}")
                            analysis_results[analysis.file_path] = analysis
                    logger.info("Background analysis task completed successfully")
                except Exception as e:
                    logger.error(f"Error in background analysis task: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise
            
            # Start the background task
            task = asyncio.create_task(run_analysis())
            logger.info(f"Created background task: {task}")
            
            response_data = {
                "message": "Analysis started successfully",
                "status": "running",
                "task_id": str(id(task))
            }
            return JSONResponse(
                content=jsonable_encoder(response_data),
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
            
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        response_data = {
            "message": f"Error starting analysis: {str(e)}",
            "status": "error",
            "error": str(e)
        }
        return JSONResponse(
            content=jsonable_encoder(response_data),
            status_code=500,
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

@app.get("/api/analyze/progress", response_model=AnalysisProgressModel)
async def get_analysis_progress():
    """Get the current progress of code analysis."""
    try:
        logger.debug("Getting analysis progress")
        progress = await code_analyzer.get_analysis_progress()
        logger.debug(f"Current progress: {vars(progress)}")
        
        # Create the response model
        response = AnalysisProgressModel(
            total_files=progress.total_files,
            analyzed_files=progress.analyzed_files,
            current_file=progress.current_file,
            status=progress.status,
            error_message=progress.error_message
        )
        
        logger.debug(f"Progress response: {vars(response)}")
        
        # Add headers to prevent caching
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        return JSONResponse(
            content=jsonable_encoder(response),
            headers=headers
        )
    except Exception as e:
        logger.error(f"Error getting analysis progress: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return a valid response even in case of error
        return JSONResponse(
            content=jsonable_encoder(AnalysisProgressModel(
                total_files=0,
                analyzed_files=0,
                status="error",
                error_message=str(e)
            )),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

@app.get("/api/analyze/results")
async def get_analysis_results():
    """Get the results of the code analysis."""
    try:
        logger.debug("Getting analysis results")
        if not analysis_results:
            logger.debug("No current results, attempting to load from cache")
            cached = load_latest_analysis()
            if cached:
                logger.info(f"Loaded {len(cached)} results from cache")
                analysis_results.update(cached)
            else:
                logger.warning("No cached results found")
                return JSONResponse(
                    content=jsonable_encoder({
                        "results": {},
                        "status": "no_results"
                    }),
                    headers={
                        "Content-Type": "application/json",
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0"
                    }
                )

        # Convert to serializable format
        results = {}
        for file_path, analysis in analysis_results.items():
            try:
                results[file_path] = {
                    "file_path": analysis.file_path,
                    "language": analysis.language,
                    "purpose": analysis.purpose,
                    "key_functionality": analysis.key_functionality,
                    "dependencies": analysis.dependencies,
                    "interfaces": analysis.interfaces,
                    "implementation_details": analysis.implementation_details,
                    "potential_issues": analysis.potential_issues,
                    "domain": analysis.domain
                }
            except Exception as e:
                logger.error(f"Error converting analysis for {file_path}: {e}")
                continue

        logger.debug(f"Returning {len(results)} analysis results")
        return JSONResponse(
            content=jsonable_encoder({
                "results": results,
                "status": "success"
            }),
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            content=jsonable_encoder({
                "results": {},
                "status": "error",
                "error": str(e)
            }),
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

@app.get("/api/analyze/file/{file_path:path}")
async def analyze_single_file(file_path: str):
    """Analyze a single file."""
    try:
        analysis = await code_analyzer.analyze_file(os.path.join(WORKSPACE_DIR, file_path))
        if not analysis:
            raise HTTPException(status_code=404, detail="File not found or cannot be analyzed")
            
        return FileAnalysisModel(
            file_path=analysis.file_path,
            language=analysis.language,
            purpose=analysis.purpose,
            key_functionality=analysis.key_functionality,
            dependencies=analysis.dependencies,
            interfaces=analysis.interfaces,
            implementation_details=analysis.implementation_details,
            potential_issues=analysis.potential_issues,
            domain=analysis.domain
        )
    except Exception as e:
        logger.error(f"Error analyzing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/generate-requirements")
async def generate_requirements_from_analysis(request: GenerateRequirementsRequest):
    """Generate requirements based on code analysis results."""
    try:
        # Load latest results if current results are empty
        if not analysis_results:
            loaded_results = load_latest_analysis()
            if loaded_results:
                analysis_results.update(loaded_results)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No analysis results available. Please run analysis first."
                )
        
        # Filter analyses for the specified domain
        domain_analyses = [
            analysis for analysis in analysis_results.values()
            if analysis.domain == request.domain
        ]
        
        if not domain_analyses:
            raise HTTPException(
                status_code=404,
                detail=f"No analyzed files found for domain: {request.domain}"
            )
            
        # Prepare context from analyses
        context = f"""Based on code analysis, this domain contains {len(domain_analyses)} files.
Key purposes and functionality:

{chr(10).join(f"- {analysis.purpose}" for analysis in domain_analyses)}

Key dependencies and interfaces:
{chr(10).join(f"- {dep}" for analysis in domain_analyses for dep in analysis.dependencies)}

Implementation patterns:
{chr(10).join(f"- {detail}" for analysis in domain_analyses for detail in analysis.implementation_details)}
"""
        
        # Generate requirements
        requirements = await ai_service.generate_requirements(request.domain, context)
        return requirements
        
    except Exception as e:
        logger.error(f"Error generating requirements from analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))