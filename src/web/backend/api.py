"""API endpoints for the PLM system."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import jsonschema
import yaml
import logging
from .services.requirements_parser import RequirementsParser, Requirement
from .services.code_analyzer import CodeAnalyzerService
from .services.architecture import Block, load_or_create_architecture, generate_architecture_from_analysis
from .schemas import REQUIREMENT_SCHEMA, FILE_ANALYSIS_SCHEMA, FUNCTION_INFO_SCHEMA
from pathlib import Path
import traceback
from fastapi.responses import JSONResponse

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(title="PLM API", version="1.0.0")

# Update CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

class DomainInfo(BaseModel):
    """Model for domain information."""
    name: str
    description: str
    subdomain_ids: List[str]

# Settings model
class Settings(BaseModel):
    """Model for PLM settings."""
    source_folder: str = "src"
    requirements_folder: str = "requirements"
    architecture_folder: str = "architecture"
    folder_structure: str = "hierarchical"
    preferred_languages: List[str] = ["python", "javascript", "cpp"]
    custom_llm_instructions: str = ""
    source_include_patterns: List[str] = [
        "**/*.py", "**/*.js", "**/*.ts",  # Web languages
        "**/*.cpp", "**/*.hpp", "**/*.h"  # C/C++
    ]
    source_exclude_patterns: List[str] = [
        "**/node_modules/**", "**/__pycache__/**", "**/venv/**",
        "**/build/**", "**/dist/**"
    ]
    domains: Dict[str, DomainInfo] = {}

class RequirementCreate(BaseModel):
    """Model for creating a requirement."""
    id: str = Field(..., pattern="^RQ-[A-Z_]+-\\d+$")
    domain: str
    description: str
    linked_blocks: List[str] = Field(default_factory=list)
    additional_notes: List[str] = Field(default_factory=list)
    implementation_files: List[str] = Field(default_factory=list)

class RequirementResponse(BaseModel):
    """Model for requirement response."""
    id: str
    domain: str
    description: str
    linked_blocks: List[str]
    additional_notes: List[str]
    implementation_files: List[str]
    code_references: List[Dict] = Field(default_factory=list)

class FileAnalysisResponse(BaseModel):
    """Model for file analysis response."""
    purpose: str
    key_functionality: List[str]
    dependencies: List[str]
    implementation_details: List[str]
    potential_issues: List[str]
    functions: List[Dict] = Field(default_factory=list)

class ArchitectureNode(BaseModel):
    """Model for architecture diagram node."""
    id: str
    label: str
    type: str = "default"
    data: Dict = Field(default_factory=dict)

class ArchitectureEdge(BaseModel):
    """Model for architecture diagram edge."""
    id: str
    source: str
    target: str
    label: str = ""
    type: str = "default"

class ArchitectureResponse(BaseModel):
    """Model for architecture diagram response."""
    nodes: List[ArchitectureNode] = Field(default_factory=list)
    edges: List[ArchitectureEdge] = Field(default_factory=list)

class DomainRecommendation(BaseModel):
    """Model for domain recommendation."""
    domain_id: str
    name: str
    description: str
    subdomain_ids: List[str]
    confidence: float
    matching_files: List[str]
    reasons: List[str]
    reasoning: str

class DomainRecommendationsResponse(BaseModel):
    """Model for domain recommendations response."""
    recommendations: List[DomainRecommendation]
    changes_detected: bool = Field(default=False)

class AnalysisStartRequest(BaseModel):
    """Model for starting code analysis."""
    files: Optional[List[str]] = None  # If None, analyze all files

class AnalysisStartResponse(BaseModel):
    """Model for analysis start response."""
    status: str = "started"
    message: str
    total_files: int

class AnalysisProgressResponse(BaseModel):
    """Model for analysis progress response."""
    status: str
    progress: float
    current_file: Optional[str] = None
    total_files: int
    completed_files: int
    message: str

def get_requirements_parser():
    """Dependency injection for requirements parser."""
    return RequirementsParser()

def get_code_analyzer():
    """Dependency injection for code analyzer."""
    if not hasattr(get_code_analyzer, '_instance'):
        get_code_analyzer._instance = CodeAnalyzerService()
    return get_code_analyzer._instance

@app.get("/api/settings", response_model=Settings)
async def get_settings(analyzer: CodeAnalyzerService = Depends(get_code_analyzer)):
    """Get PLM settings."""
    try:
        return Settings(**analyzer.settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/settings", response_model=Settings)
async def update_settings(
    settings: Settings,
    analyzer: CodeAnalyzerService = Depends(get_code_analyzer)
):
    """Update PLM settings."""
    try:
        # Update settings file
        with open(analyzer.settings_path, "w") as f:
            settings_dict = settings.dict()
            yaml.safe_dump(settings_dict, f)
        
        # Reload settings in analyzer
        analyzer.settings = settings_dict
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/requirements", response_model=List[RequirementResponse])
async def list_requirements(parser: RequirementsParser = Depends(get_requirements_parser)):
    """List all requirements."""
    logger.info("GET /api/requirements - Fetching all requirements")
    try:
        requirements = parser.parse_all()
        logger.info(f"Found {len(requirements)} requirements")
        logger.debug(f"Requirements: {requirements}")
        response_data = [RequirementResponse(**req.to_dict()) for req in requirements.values()]
        logger.info(f"Returning {len(response_data)} requirements")
        return response_data
    except Exception as e:
        logger.error(f"Error fetching requirements: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/requirements/{req_id}", response_model=RequirementResponse)
async def get_requirement(
    req_id: str,
    parser: RequirementsParser = Depends(get_requirements_parser)
):
    """Get a specific requirement by ID."""
    logger.info(f"GET /api/requirements/{req_id} - Fetching requirement")
    try:
        requirements = parser.parse_all()
        logger.debug(f"All requirements: {requirements}")
        if req_id not in requirements:
            logger.warning(f"Requirement {req_id} not found")
            raise HTTPException(status_code=404, detail=f"Requirement {req_id} not found")
        response_data = RequirementResponse(**requirements[req_id].to_dict())
        logger.info(f"Returning requirement {req_id}")
        return response_data
    except Exception as e:
        logger.error(f"Error fetching requirement {req_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/requirements", response_model=RequirementResponse)
async def create_requirement(
    req: RequirementCreate,
    parser: RequirementsParser = Depends(get_requirements_parser)
):
    """Create a new requirement."""
    logger.info(f"POST /api/requirements - Creating requirement {req.id}")
    try:
        # Convert to dict for validation
        req_dict = req.dict()
        logger.debug(f"Requirement data: {req_dict}")
        jsonschema.validate(instance=req_dict, schema=REQUIREMENT_SCHEMA)
        
        # Create requirement
        requirement = Requirement(**req_dict)
        parser.save_requirement(requirement)
        logger.info(f"Successfully created requirement {req.id}")
        return RequirementResponse(**requirement.to_dict())
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Validation error for requirement {req.id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating requirement {req.id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/requirements/{req_id}", response_model=RequirementResponse)
async def update_requirement(
    req_id: str,
    req: RequirementCreate,
    parser: RequirementsParser = Depends(get_requirements_parser)
):
    """Update an existing requirement."""
    try:
        requirements = parser.parse_all()
        if req_id not in requirements:
            raise HTTPException(status_code=404, detail=f"Requirement {req_id} not found")
        
        # Validate and update
        req_dict = req.dict()
        jsonschema.validate(instance=req_dict, schema=REQUIREMENT_SCHEMA)
        
        requirement = Requirement(**req_dict)
        parser.save_requirement(requirement)
        return RequirementResponse(**requirement.to_dict())
    except jsonschema.exceptions.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/requirements/{req_id}")
async def delete_requirement(
    req_id: str,
    parser: RequirementsParser = Depends(get_requirements_parser)
):
    """Delete a requirement."""
    try:
        requirements = parser.parse_all()
        if req_id not in requirements:
            raise HTTPException(status_code=404, detail=f"Requirement {req_id} not found")
        
        # Get the file path
        requirement = requirements[req_id]
        domain_path = requirement.domain.split('/')
        req_file = parser.requirements_dir.joinpath(*domain_path, f"{req_id.lower()}.yaml")
        
        # Delete the file
        if req_file.exists():
            req_file.unlink()
            return {"message": f"Requirement {req_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail=f"Requirement file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze/file/{file_path:path}", response_model=FileAnalysisResponse)
async def analyze_file(
    file_path: str,
    analyzer: CodeAnalyzerService = Depends(get_code_analyzer)
):
    """Analyze a specific file."""
    try:
        analysis = analyzer.analyze_file(file_path)
        
        # Validate analysis results
        jsonschema.validate(instance=analysis, schema=FILE_ANALYSIS_SCHEMA)
        
        # Validate function info if present
        if "functions" in analysis:
            for func in analysis["functions"]:
                jsonschema.validate(instance=func, schema=FUNCTION_INFO_SCHEMA)
        
        return FileAnalysisResponse(**analysis)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File {file_path} not found")
    except jsonschema.exceptions.ValidationError as e:
        raise HTTPException(status_code=500, detail=f"Invalid analysis result: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze/results")
async def get_analysis_results(analyzer: CodeAnalyzerService = Depends(get_code_analyzer)):
    """Get cached analysis results."""
    try:
        results = analyzer.analysis_state.get('results', {})
        if not results:
            # Try to load from cache if no results in memory
            analyzer._load_cached_results()
            results = analyzer.analysis_state.get('results', {})
            
        return results
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/architecture", response_model=ArchitectureResponse)
async def get_architecture(analyzer: CodeAnalyzerService = Depends(get_code_analyzer)):
    """Get architecture diagram data."""
    try:
        # Create nodes for each domain
        nodes = []
        edges = []
        
        for domain_id, domain_info in analyzer.settings.get('domains', {}).items():
            # Add domain node
            nodes.append(ArchitectureNode(
                id=domain_id,
                label=domain_info.get('name', domain_id),
                type="domain",
                data={
                    "description": domain_info.get('description', ''),
                    "type": "domain"
                }
            ))
            
            # Add subdomain nodes and edges
            for subdomain_id in domain_info.get('subdomain_ids', []):
                node_id = f"{domain_id}_{subdomain_id}"
                nodes.append(ArchitectureNode(
                    id=node_id,
                    label=subdomain_id,
                    type="subdomain",
                    data={
                        "parent": domain_id,
                        "type": "subdomain"
                    }
                ))
                edges.append(ArchitectureEdge(
                    id=f"edge_{domain_id}_{subdomain_id}",
                    source=domain_id,
                    target=node_id,
                    type="contains"
                ))
        
        return ArchitectureResponse(nodes=nodes, edges=edges)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/recommend-domains", response_model=DomainRecommendationsResponse)
async def recommend_domains(analyzer: CodeAnalyzerService = Depends(get_code_analyzer)):
    """Recommend domains based on code analysis."""
    try:
        recommendations = []
        domains = analyzer.settings.get('domains', {})
        
        # For each domain, check if there are files that match its description
        for domain_id, domain_info in domains.items():
            # Get domain keywords from description
            description = domain_info.get('description', '').lower()
            name = domain_info.get('name', '').lower()
            
            # Find matching files
            matching_files = []
            confidence = 0.0
            reasons = []
            
            # Check source files for matches
            source_dir = analyzer.workspace_dir / analyzer.settings.get('source_folder', 'src')
            if source_dir.exists():
                for file_path in source_dir.rglob('*'):
                    if not analyzer._should_include_file(str(file_path)):
                        continue
                        
                    # Simple keyword matching for now
                    # TODO: Use more sophisticated matching with AI
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            
                            # Check for domain keywords in content
                            keyword_matches = []
                            for keyword in description.split():
                                if len(keyword) > 3 and keyword in content:  # Skip short words
                                    keyword_matches.append(keyword)
                            
                            if keyword_matches:
                                rel_path = file_path.relative_to(analyzer.workspace_dir)
                                matching_files.append(str(rel_path))
                                reasons.append(f"Found keywords: {', '.join(keyword_matches)}")
                    except Exception as e:
                        continue
            
            # Calculate confidence based on matching files
            if matching_files:
                confidence = min(0.8, 0.3 + (len(matching_files) * 0.1))  # Cap at 0.8
                
                recommendations.append(DomainRecommendation(
                    domain_id=domain_id,
                    name=domain_info.get('name', domain_id),
                    description=domain_info.get('description', ''),
                    subdomain_ids=domain_info.get('subdomain_ids', []),
                    confidence=confidence,
                    matching_files=matching_files,
                    reasons=reasons,
                    reasoning=f"Found {len(matching_files)} files with matching keywords from the domain description."
                ))
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        # Determine if changes are recommended
        changes_detected = any(r.confidence > 0.5 for r in recommendations)
        
        return DomainRecommendationsResponse(
            recommendations=recommendations,
            changes_detected=changes_detected
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/start", response_model=AnalysisStartResponse)
async def start_analysis(
    request: AnalysisStartRequest,
    analyzer: CodeAnalyzerService = Depends(get_code_analyzer)
):
    """Start code analysis for all or selected files."""
    try:
        source_dir = Path(analyzer.workspace_dir) / analyzer.settings.get('source_folder', 'src')
        
        # Get list of files to analyze
        files_to_analyze = []
        if request.files:
            # Analyze specific files
            for file_path in request.files:
                full_path = source_dir / file_path
                if full_path.exists() and analyzer._should_include_file(str(full_path)):
                    files_to_analyze.append(str(full_path))
        else:
            # Analyze all files
            for file_path in source_dir.rglob('*'):
                if analyzer._should_include_file(str(file_path)):
                    files_to_analyze.append(str(file_path))
        
        if not files_to_analyze:
            raise HTTPException(
                status_code=400,
                detail="No valid files found to analyze"
            )
        
        # Store analysis state
        analyzer.analysis_state = {
            "status": "in_progress",
            "total_files": len(files_to_analyze),
            "completed_files": 0,
            "current_file": None,
            "files_to_analyze": files_to_analyze,
            "results": {}
        }
        
        # Start background analysis task
        analyzer.start_analysis_task()
        
        return AnalysisStartResponse(
            status="started",
            message=f"Analysis started for {len(files_to_analyze)} files",
            total_files=len(files_to_analyze)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze/progress", response_model=AnalysisProgressResponse)
async def get_analysis_progress(
    analyzer: CodeAnalyzerService = Depends(get_code_analyzer)
):
    """Get the current progress of code analysis."""
    try:
        state = analyzer.analysis_state
        if not state:
            logger.debug("No analysis state found, returning not_started status")
            return AnalysisProgressResponse(
                status="not_started",
                progress=0.0,
                total_files=0,
                completed_files=0,
                message="Analysis has not been started"
            )
        
        total_files = state.get('total_files', 0)
        completed_files = state.get('completed_files', 0)
        progress = (completed_files / total_files * 100) if total_files > 0 else 0
        
        logger.debug(f"Analysis progress - Status: {state.get('status')}, Progress: {progress}%, "
                    f"Completed: {completed_files}/{total_files}")
        
        return AnalysisProgressResponse(
            status=state.get('status', 'unknown'),
            progress=progress,
            current_file=state.get('current_file'),
            total_files=total_files,
            completed_files=completed_files,
            message=state.get('message', f"Analyzed {completed_files} of {total_files} files")
        )
        
    except Exception as e:
        logger.error(f"Error getting analysis progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/generate-requirements")
async def generate_requirements(
    request: AnalysisStartRequest,
    analyzer: CodeAnalyzerService = Depends(get_code_analyzer),
    parser: RequirementsParser = Depends(get_requirements_parser)
):
    """Generate requirements based on code analysis."""
    try:
        # Get analysis results
        results = analyzer.analysis_state.get('results', {})
        if not results:
            raise HTTPException(
                status_code=400,
                detail="No analysis results available. Please run code analysis first."
            )

        # Filter results if specific files were requested
        if request.files:
            results = {k: v for k, v in results.items() if k in request.files}

        # Get available domains from settings
        available_domains = list(analyzer.settings.get('domains', {}).keys())
        if not available_domains:
            raise HTTPException(
                status_code=400,
                detail="No domains configured in settings. Please configure domains first."
            )

        # Generate requirements for each domain
        generated_requirements = []
        generated_files = []

        # Group files by domain
        domain_files = {}
        for file_path, analysis in results.items():
            # If domain is None, let AI service determine the domain
            domain = analysis.get('domain')
            if domain is None:
                # Create context for domain determination
                file_context = (
                    f"File: {file_path}\n"
                    f"Purpose: {analysis.get('purpose', '')}\n"
                    f"Key Functionality: {', '.join(analysis.get('key_functionality', []))}\n"
                    f"Implementation Details: {', '.join(analysis.get('implementation_details', []))}"
                )
                domain = await analyzer.ai_service.determine_domain(file_context, available_domains)
                if domain is None:
                    domain = "unknown"  # Fallback if AI can't determine domain
            
            if domain not in domain_files:
                domain_files[domain] = []
            domain_files[domain].append((file_path, analysis))

        # Generate requirements for each domain
        for domain, files in domain_files.items():
            if domain == "unknown":
                continue  # Skip files with unknown domain
                
            # Prepare context for requirement generation
            context = "\n\n".join([
                f"File: {file_path}\n"
                f"Purpose: {analysis.get('purpose', '')}\n"
                f"Key Functionality: {', '.join(analysis.get('key_functionality', []))}\n"
                f"Implementation Details: {', '.join(analysis.get('implementation_details', []))}"
                for file_path, analysis in files
            ])

            # Generate requirements using AI service
            domain_requirements = await analyzer.ai_service.generate_requirements(domain, context)
            
            # Save generated requirements
            for req in domain_requirements:
                # Add implementation files
                req.implementation_files = [file_path for file_path, _ in files]
                # Convert GeneratedRequirement to Requirement
                requirement = Requirement(
                    id=req.id,
                    domain=req.domain,
                    description=req.description,
                    linked_blocks=req.linked_blocks,
                    additional_notes=req.additional_notes,
                    implementation_files=req.implementation_files
                )
                parser.save_requirement(requirement)
                generated_requirements.append(requirement)
                generated_files.append(f"requirements/{domain}/{req.id.lower()}.yaml")

        return {
            "status": "success",
            "requirements": [
                {
                    "id": req.id,
                    "domain": req.domain,
                    "description": req.description,
                    "linked_blocks": req.linked_blocks,
                    "additional_notes": req.additional_notes,
                    "implementation_files": req.implementation_files,
                    "code_references": []  # Add empty code references as expected by frontend
                }
                for req in generated_requirements
            ],
            "generated_files": generated_files
        }

    except Exception as e:
        logger.error(f"Error generating requirements: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/architecture/generate")
async def generate_architecture():
    """Generate system architecture from latest code analysis results."""
    try:
        analyzer = get_code_analyzer()
        # Get results from analysis state instead of non-existent method
        results = analyzer.analysis_state.get('results', {})
        if not results:
            return JSONResponse(
                status_code=400,
                content={"error": "No code analysis results available. Please run code analysis first."}
            )
        
        # Convert analysis results to the expected format
        formatted_results = {}
        for file_path, file_info in results.items():
            if 'functions' in file_info:
                formatted_results[file_path] = file_info['functions']
        
        logger.info(f"Generating architecture from {len(formatted_results)} files")
        
        # Generate architecture
        architecture = generate_architecture_from_analysis(formatted_results)
        
        # Convert to API response format
        response = {
            "blocks": {},
            "root_id": architecture.block_id
        }
        
        def add_block_to_response(block: Block):
            response["blocks"][block.block_id] = {
                "name": block.name,
                "domain": block.domain,
                "description": block.description,
                "requirements": block.requirements,
                "subblocks": [b.block_id for b in block.subblocks],
                "x": block.x,
                "y": block.y
            }
            for subblock in block.subblocks:
                add_block_to_response(subblock)
        
        add_block_to_response(architecture)
        logger.info(f"Generated architecture with {len(response['blocks'])} blocks")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating architecture: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate architecture: {str(e)}"}
        )

# Add a test endpoint to verify API is accessible
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called")
    return {"status": "ok"}