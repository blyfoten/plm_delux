from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import os
import frontmatter
import sys
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_api.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from ai_integration import OpenAIService, MockAIService, GeneratedRequirement, GeneratedCode
from requirements_parser import RequirementsParser, Requirement
from architecture import Block, system_architecture
from visualizer import ArchitectureVisualizer

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
parser = RequirementsParser("requirements")

# Use MockAIService if no API key is available
api_key = os.getenv("OPENAI_API_KEY")
ai = OpenAIService(api_key) if api_key else MockAIService()

visualizer = ArchitectureVisualizer(parser.parse_all())

# Models for API requests/responses
class RequirementRequest(BaseModel):
    domain: str
    context: str

class RequirementUpdate(BaseModel):
    id: str
    domain: str
    description: str
    linked_blocks: List[str]
    content: str

class CodeGenerationRequest(BaseModel):
    requirement_id: str

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

@app.on_event("startup")
async def startup_event():
    """Log when the API server starts up."""
    logger.info("=== API Server Starting Up ===")
    logger.info(f"Using AI Service: {ai.__class__.__name__}")
    logger.info(f"Requirements directory: {parser.requirements_dir}")

@app.get("/api/requirements")
async def get_requirements():
    """Get all requirements."""
    logger.info("Fetching all requirements")
    try:
        requirements = parser.parse_all()
        logger.info(f"Found {len(requirements)} requirements")
        return {"requirements": requirements}
    except Exception as e:
        logger.error(f"Error fetching requirements: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/requirements/{requirement_id}")
async def get_requirement(requirement_id: str):
    """Get a specific requirement."""
    requirements = parser.parse_all()
    if requirement_id not in requirements:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirements[requirement_id]

@app.put("/api/requirements/{requirement_id}")
async def update_requirement(requirement_id: str, requirement: RequirementUpdate):
    """Update a requirement."""
    try:
        # Find the requirement file
        requirement_file = None
        for root, _, files in os.walk("requirements"):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        post = frontmatter.load(f)
                        if post.metadata.get('id') == requirement_id:
                            requirement_file = file_path
                            break
            if requirement_file:
                break

        if not requirement_file:
            raise HTTPException(status_code=404, detail="Requirement file not found")

        # Update the requirement file
        with open(requirement_file, 'w') as f:
            f.write('---\n')
            f.write(f'id: {requirement.id}\n')
            f.write(f'domain: {requirement.domain}\n')
            f.write(f'linked_blocks: {requirement.linked_blocks}\n')
            f.write(f'description: "{requirement.description}"\n')
            f.write('---\n\n')
            f.write(requirement.content)

        return {"message": "Requirement updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/requirements/generate")
async def generate_requirements(request: dict):
    """Generate new requirements."""
    domain = request.get("domain")
    context = request.get("context")
    logger.info(f"Generating requirements for domain: {domain}")
    logger.info(f"Context: {context}")
    
    try:
        requirements = await ai.generate_requirements(domain, context)
        logger.info(f"Generated {len(requirements)} requirements")
        
        # Save requirements
        domain_dir = Path("requirements") / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        for req in requirements:
            logger.info(f"Saving requirement: {req.id}")
            filepath = domain_dir / f"{req.id.lower()}.md"
            with open(filepath, "w") as f:
                f.write("---\n")
                f.write(f"id: {req.id}\n")
                f.write(f"domain: {req.domain}\n")
                f.write(f"linked_blocks: {req.linked_blocks}\n")
                f.write(f'description: "{req.description}"\n')
                f.write("---\n\n")
                f.write(f"# Requirement {req.id}\n\n")
                f.write("**Description:**  \n")
                f.write(f"{req.description}\n\n")
                f.write("**Additional Notes:**  \n")
                for note in req.additional_notes:
                    f.write(f"- {note}\n")
        
        return {"message": "Requirements generated successfully", "requirements": requirements}
    except Exception as e:
        logger.error(f"Error generating requirements: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/code/generate")
async def generate_code(request: dict):
    """Generate code for a requirement."""
    requirement_id = request.get("requirement_id")
    logger.info(f"Generating code for requirement: {requirement_id}")
    
    try:
        requirements = parser.parse_all()
        if requirement_id not in requirements:
            logger.error(f"Requirement not found: {requirement_id}")
            raise HTTPException(status_code=404, detail=f"Requirement {requirement_id} not found")
        
        requirement = requirements[requirement_id]
        logger.info(f"Found requirement: {requirement['description']}")
        
        generated = await ai.generate_code(requirement)
        logger.info(f"Generated code for block: {generated.block_id}")
        
        # Add tests
        generated = await ai.enhance_code_with_tests(generated)
        logger.info("Added tests to generated code")
        
        # Save the generated code
        output_dir = Path("src/generated") / generated.block_id.lower()
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
        
        return {"message": "Code generated successfully", "files": [str(impl_file)]}
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/architecture")
async def get_architecture():
    """Get system architecture."""
    logger.info("Fetching system architecture")
    try:
        return convert_architecture_to_dict(system_architecture)
    except Exception as e:
        logger.error(f"Error fetching architecture: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/architecture")
async def update_architecture(request: ArchitectureUpdateRequest):
    """Update the architecture based on visual editor changes."""
    try:
        update_system_architecture(request.blocks)
        
        # Regenerate visualization
        parser = RequirementsParser("requirements")
        requirements = parser.parse_all()
        visualizer = ArchitectureVisualizer(requirements)
        visualizer.generate_diagram(system_architecture, "docs/architecture")
        
        return {"message": "Architecture updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/architecture/improve")
async def improve_architecture():
    """Get AI suggestions for improving the architecture."""
    try:
        current_arch = str(system_architecture)
        suggestions = await ai.suggest_architecture_improvements(current_arch)
        
        # Save suggestions
        with open('docs/architecture_suggestions.md', 'w') as f:
            f.write('# Architecture Improvement Suggestions\n\n')
            f.write(suggestions)
        
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def save_requirements(requirements: List[GeneratedRequirement], domain: str):
    """Save generated requirements to files."""
    domain_dir = os.path.join('requirements', domain)
    os.makedirs(domain_dir, exist_ok=True)
    
    for req in requirements:
        filename = f"{req.id.lower()}.md"
        filepath = os.path.join(domain_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write('---\n')
            f.write(f'id: {req.id}\n')
            f.write(f'domain: {req.domain}\n')
            f.write(f'linked_blocks: {req.linked_blocks}\n')
            f.write(f'description: "{req.description}"\n')
            f.write('---\n\n')
            f.write(f'# Requirement {req.id}\n\n')
            f.write('**Description:**  \n')
            f.write(f'{req.description}\n\n')
            f.write('**Additional Notes:**  \n')
            for note in req.additional_notes:
                f.write(f'- {note}\n')

def save_generated_code(generated: GeneratedCode):
    """Save generated code to file."""
    output_dir = os.path.join('src', 'generated', generated.block_id.lower())
    os.makedirs(output_dir, exist_ok=True)
    
    impl_file = os.path.join(output_dir, 'implementation.py')
    with open(impl_file, 'w') as f:
        f.write(generated.code)

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

def update_system_architecture(blocks: Dict[str, ArchitectureBlock]):
    """Update system architecture based on visual editor changes."""
    def update_block(block: Block, block_data: ArchitectureBlock):
        block.name = block_data.name
        block.requirements = block_data.requirements
        block.x = block_data.x
        block.y = block_data.y
        
        # Update subblocks
        new_subblocks = []
        for subblock_id in block_data.subblocks:
            if subblock_id in blocks:
                subblock = next((b for b in block.subblocks if b.block_id == subblock_id), None)
                if not subblock:
                    subblock = Block(subblock_id, blocks[subblock_id].name)
                update_block(subblock, blocks[subblock_id])
                new_subblocks.append(subblock)
        block.subblocks = new_subblocks
    
    # Update the system architecture
    if system_architecture.block_id in blocks:
        update_block(system_architecture, blocks[system_architecture.block_id]) 

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_service": ai.__class__.__name__,
        "requirements_dir": str(parser.requirements_dir)
    } 