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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from ai_integration import OpenAIService, MockAIService, GeneratedRequirement, GeneratedCode
from requirements_parser import RequirementsParser, Requirement
from architecture import Block, system_architecture, save_architecture
from visualizer import ArchitectureVisualizer
from requirements_mapper import RequirementsMapper, CodeReference

# Get workspace directory from environment or use default
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/work")

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

class PLMSettings(BaseModel):
    """Settings model for PLM."""
    source_folder: str = "src"
    requirements_folder: str = "requirements"
    architecture_folder: str = "architecture"
    generated_folder: str = "generated"
    folder_structure: str = "hierarchical"  # or "flat"
    preferred_languages: List[str] = ["python", "javascript"]
    custom_llm_instructions: str = ""
    source_include_patterns: List[str] = ["**/*.py", "**/*.js", "**/*.ts"]
    source_exclude_patterns: List[str] = ["**/node_modules/**", "**/__pycache__/**", "**/venv/**"]

    @classmethod
    def get_default_settings(cls) -> "PLMSettings":
        """Get default settings with comments."""
        return cls()

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
source_folder: {source_folder}
requirements_folder: {requirements_folder}
architecture_folder: {architecture_folder}
generated_folder: {generated_folder}

# Folder structure preference (hierarchical or flat)
folder_structure: {folder_structure}

# Preferred programming languages for code generation
preferred_languages:
{languages}

# Custom instructions for LLM interactions
custom_llm_instructions: {custom_llm_instructions}

# Source code scanning patterns
source_include_patterns:
{includes}

# Patterns to exclude from source scanning
source_exclude_patterns:
{excludes}
""".format(
        source_folder=settings_dict["source_folder"],
        requirements_folder=settings_dict["requirements_folder"],
        architecture_folder=settings_dict["architecture_folder"],
        generated_folder=settings_dict["generated_folder"],
        folder_structure=settings_dict["folder_structure"],
        languages="\n".join(f"  - {lang}" for lang in settings_dict["preferred_languages"]),
        custom_llm_instructions=settings_dict["custom_llm_instructions"],
        includes="\n".join(f"  - {pattern}" for pattern in settings_dict["source_include_patterns"]),
        excludes="\n".join(f"  - {pattern}" for pattern in settings_dict["source_exclude_patterns"])
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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
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
        
        # Log the exact structure being passed to generate_code
        logger.info(f"Calling ai.generate_code with dict: {requirement_dict}")
        generated = await ai.generate_code(requirement_dict)
        logger.info(f"Generated code for block: {generated.block_id}")
        
        # Add tests
        generated = await ai.enhance_code_with_tests(generated)
        logger.info("Added tests to generated code")
        
        # Save the generated code
        output_dir = Path(WORKSPACE_DIR) / "generated" / generated.block_id.lower()
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
        return load_settings()
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/settings")
async def update_settings(new_settings: PLMSettings):
    """Update PLM settings."""
    logger.info("Updating settings")
    try:
        save_settings(new_settings)
        return {"message": "Settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 