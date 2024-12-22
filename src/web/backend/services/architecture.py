"""System architecture definition and validation."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from pathlib import Path
import json
import logging
from .code_analyzer import FunctionInfo

logger = logging.getLogger(__name__)

@dataclass
class Block:
    """Architecture block definition."""
    block_id: str
    name: str
    domain: Optional[str] = None
    description: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    subblocks: List['Block'] = field(default_factory=list)
    x: float = 0
    y: float = 0

    def validate(self) -> List[str]:
        """Validate the block and its subblocks."""
        errors = []
        
        # Validate block ID format
        if not self.block_id.startswith('BLK-'):
            errors.append(f"Block ID '{self.block_id}' must start with 'BLK-'")
        
        # Check for duplicate block IDs
        block_ids = set()
        def check_duplicate_ids(block: Block):
            if block.block_id in block_ids:
                errors.append(f"Duplicate block ID: {block.block_id}")
            block_ids.add(block.block_id)
            for subblock in block.subblocks:
                check_duplicate_ids(subblock)
        
        check_duplicate_ids(self)
        
        # Validate requirement references
        for req in self.requirements:
            if not req.startswith('RQ-'):
                errors.append(f"Invalid requirement ID format: {req}")
        
        # Validate subblocks
        for subblock in self.subblocks:
            errors.extend(subblock.validate())
        
        return errors

    def to_dict(self) -> Dict:
        """Convert block to dictionary representation."""
        return {
            "block_id": self.block_id,
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "requirements": self.requirements,
            "subblocks": [b.to_dict() for b in self.subblocks],
            "x": self.x,
            "y": self.y
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Block':
        """Create block from dictionary representation."""
        return cls(
            block_id=data["block_id"],
            name=data["name"],
            domain=data.get("domain"),
            description=data.get("description"),
            requirements=data.get("requirements", []),
            subblocks=[cls.from_dict(b) for b in data.get("subblocks", [])],
            x=data.get("x", 0),
            y=data.get("y", 0)
        )
    
    def find_block(self, block_id: str) -> Optional['Block']:
        """Find a block by ID in this block's hierarchy."""
        if self.block_id == block_id:
            return self
        for subblock in self.subblocks:
            found = subblock.find_block(block_id)
            if found:
                return found
        return None
    
    def get_all_requirements(self) -> Set[str]:
        """Get all requirements referenced in this block's hierarchy."""
        reqs = set(self.requirements)
        for subblock in self.subblocks:
            reqs.update(subblock.get_all_requirements())
        return reqs

def generate_architecture_from_analysis(analysis_results: Dict[str, List[FunctionInfo]], workspace_dir: str = "/work") -> Block:
    """Generate system architecture from code analysis results."""
    logger.info("Generating architecture from analysis results")
    
    # Create root block
    root = Block(
        block_id="BLK-SYSTEM",
        name="System",
        description="Auto-generated system architecture"
    )
    
    # Group functions by domain
    domain_functions: Dict[str, List[tuple[str, FunctionInfo]]] = {}
    
    for file_path, functions in analysis_results.items():
        # Get domain from file path structure
        domain = Path(file_path).parent.name.upper()
        if domain not in domain_functions:
            domain_functions[domain] = []
        for func in functions:
            domain_functions[domain].append((file_path, func))
    
    # Create blocks for each domain
    block_id_counter = 1
    for domain, functions in domain_functions.items():
        # Create domain block
        domain_block = Block(
            block_id=f"BLK-{domain}-{block_id_counter:03d}",
            name=domain,
            domain=domain,
            description=f"Functions related to {domain}"
        )
        block_id_counter += 1
        
        # Collect requirements from functions
        domain_requirements = set()
        for _, func in functions:
            if hasattr(func, 'requirements') and func.requirements:
                domain_requirements.update(func.requirements)
        domain_block.requirements = list(domain_requirements)
        
        # Add domain block to root
        root.subblocks.append(domain_block)
        
        # Group functions by module
        module_functions: Dict[str, List[tuple[str, FunctionInfo]]] = {}
        for file_path, func in functions:
            module = Path(file_path).stem  # Use filename without extension as module name
            if module not in module_functions:
                module_functions[module] = []
            module_functions[module].append((file_path, func))
        
        # Create subblocks for modules with multiple functions
        for module, module_funcs in module_functions.items():
            if len(module_funcs) > 1:  # Only create subblock if multiple functions
                module_block = Block(
                    block_id=f"BLK-{domain}-{module.upper()}-{block_id_counter:03d}",
                    name=f"{module}",
                    domain=domain,
                    description=f"{module} module functions"
                )
                block_id_counter += 1
                
                # Collect requirements from module functions
                module_requirements = set()
                for _, func in module_funcs:
                    if hasattr(func, 'requirements') and func.requirements:
                        module_requirements.update(func.requirements)
                module_block.requirements = list(module_requirements)
                
                domain_block.subblocks.append(module_block)
    
    # Save generated architecture
    save_architecture(root, workspace_dir)
    logger.info(f"Generated architecture with {len(domain_functions)} domains")
    
    return root

def load_or_create_architecture(workspace_dir: str = "/work", analysis_results: Optional[Dict[str, List[FunctionInfo]]] = None) -> Block:
    """Load architecture from workspace or create from analysis results."""
    arch_file = Path(workspace_dir) / "architecture" / "system.json"
    
    if arch_file.exists():
        logger.info(f"Loading architecture from {arch_file}")
        try:
            with open(arch_file) as f:
                return Block.from_dict(json.load(f))
        except Exception as e:
            logger.error(f"Error loading architecture: {str(e)}")
    
    if analysis_results:
        logger.info("Generating architecture from analysis results")
        return generate_architecture_from_analysis(analysis_results, workspace_dir)
    
    logger.info("Creating default architecture")
    return create_default_architecture()

def save_architecture(arch: Block, workspace_dir: str = "/work"):
    """Save architecture to workspace."""
    arch_file = Path(workspace_dir) / "architecture" / "system.json"
    arch_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving architecture to {arch_file}")
    with open(arch_file, 'w') as f:
        json.dump(arch.to_dict(), f, indent=2)

def create_default_architecture() -> Block:
    """Create a default system architecture."""
    return Block(
        block_id="BLK-SYSTEM",
        name="System",
        subblocks=[
            Block(
                block_id="BLK-DEMO",
                name="Demo Block",
                requirements=["RQ-DEMO-001"]
            )
        ]
    )

# Initialize system architecture
system_architecture = load_or_create_architecture() 