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

# Get workspace directory from environment or use default
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/work")

# Pydantic models for API
class RequirementBase(BaseModel):
    """Base model for requirements."""
    id: str
    domain: str
    description: str
    linked_blocks: List[str]
    additional_notes: List[str]
    content: str

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

class RequirementsResponse(BaseModel):
    """Response model for requirements endpoint."""
    requirements: Dict[str, RequirementBase]

class ArchitectureResponse(BaseModel):
    """Response model for architecture endpoint."""
    root_id: str
    blocks: Dict[str, ArchitectureBlock]

app = FastAPI(title="PLM Web Interface")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
parser = RequirementsParser(WORKSPACE_DIR)

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

@app.get("/api/requirements", response_model=RequirementsResponse)
async def get_requirements():
    """Get all requirements."""
    logger.info("Fetching requirements")
    try:
        requirements = parser.parse_all()
        # Convert requirements to Pydantic models
        requirements_dict = {
            req_id: RequirementBase(
                id=req.id,
                domain=req.domain,
                description=req.description,
                linked_blocks=req.linked_blocks,
                additional_notes=req.additional_notes,
                content=req.content
            ) for req_id, req in requirements.items()
        }
        return RequirementsResponse(requirements=requirements_dict)
    except Exception as e:
        logger.error(f"Error fetching requirements: {str(e)}")
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
        
        return CodeGenerationResponse(
            message="Code generated successfully",
            files=[str(impl_file)]
        )
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        logger.exception("Detailed traceback:")  # This will log the full traceback
        raise HTTPException(status_code=500, detail=str(e)) 