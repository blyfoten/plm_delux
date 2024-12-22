"""Requirements parser for PLM system."""

import os
import logging
import frontmatter
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import jsonschema
from ..schemas import REQUIREMENT_SCHEMA
import traceback
from .requirements_mapper import RequirementsMapper

logger = logging.getLogger(__name__)

@dataclass
class Requirement:
    """Requirement data model."""
    id: str
    domain: str
    description: str
    linked_blocks: List[str] = field(default_factory=list)
    additional_notes: List[str] = field(default_factory=list)
    implementation_files: List[str] = field(default_factory=list)
    content: Optional[str] = None  # Optional markdown content for backward compatibility

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        # Get code references from mapper
        mapper = RequirementsMapper()
        code_refs = mapper.get_references(self.id)
        
        # Convert code references to dictionary format with VSCode URLs
        code_references = []
        for ref in code_refs:
            ref_dict = {
                'file': ref.file,
                'line': ref.line,
                'function': ref.function,
                'type': ref.type,
                'url': mapper.get_vscode_url(ref)
            }
            code_references.append(ref_dict)
        
        return {
            'id': self.id,
            'domain': self.domain,
            'description': self.description,
            'linked_blocks': self.linked_blocks,
            'additional_notes': self.additional_notes,
            'implementation_files': self.implementation_files,
            'content': self.content,
            'code_references': code_references
        }

    def to_yaml(self) -> str:
        """Convert to YAML format."""
        data = {
            'id': self.id,
            'domain': self.domain,
            'description': self.description,
            'linked_blocks': self.linked_blocks,
            'additional_notes': self.additional_notes,
            'implementation_files': self.implementation_files
        }
        # Validate against schema before saving
        try:
            jsonschema.validate(instance=data, schema=REQUIREMENT_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Requirement validation failed: {e}")
            raise
        return yaml.dump(data, sort_keys=False)

    @classmethod
    def from_dict(cls, data: dict) -> 'Requirement':
        """Create a Requirement from a dictionary, validating against schema."""
        try:
            # Validate against schema
            jsonschema.validate(instance=data, schema=REQUIREMENT_SCHEMA)
            
            # Create instance
            return cls(
                id=data['id'],
                domain=data['domain'],
                description=data['description'],
                linked_blocks=data.get('linked_blocks', []),
                additional_notes=data.get('additional_notes', []),
                implementation_files=data.get('implementation_files', []),
                content=data.get('content')
            )
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Invalid requirement data: {e}")
            raise

class RequirementsParser:
    """Parser for requirements in YAML format."""
    
    def __init__(self, workspace_dir: str = "/work"):
        """Initialize the parser with workspace directory."""
        self.workspace_dir = Path(workspace_dir)
        self.requirements_dir = self.workspace_dir / "requirements"
        self.mapper = RequirementsMapper(workspace_dir)
        
        # Create requirements directory if it doesn't exist
        self.requirements_dir.mkdir(parents=True, exist_ok=True)
        self.requirements: Dict[str, Requirement] = {}
        
        # Create workspace structure if it doesn't exist
        self._ensure_workspace_structure()

    def _ensure_workspace_structure(self):
        """Ensure the workspace directory structure exists."""
        logger.info(f"Ensuring workspace structure in {self.workspace_dir}")
        
        # Create main directories
        self.requirements_dir.mkdir(parents=True, exist_ok=True)
        (self.workspace_dir / "architecture").mkdir(parents=True, exist_ok=True)

    def parse_all(self) -> Dict[str, Requirement]:
        """Parse all requirements from the workspace."""
        logger.info(f"Parsing requirements from {self.requirements_dir}")
        self.requirements.clear()
        
        if not self.requirements_dir.exists():
            logger.warning(f"Requirements directory not found: {self.requirements_dir}")
            logger.info("Creating demo requirements")
            self._create_demo_requirements()
            return self.requirements

        # Parse all .yaml files in subdirectories
        yaml_files = list(self.requirements_dir.glob("**/*.yaml"))
        logger.info(f"Found {len(yaml_files)} YAML files")
        
        for req_file in yaml_files:
            logger.debug(f"Parsing requirement file: {req_file}")
            try:
                with open(req_file) as f:
                    data = yaml.safe_load(f)
                    logger.debug(f"Loaded YAML data: {data}")
                    
                # Create requirement object with validation
                try:
                    requirement = Requirement.from_dict(data)
                    self.requirements[requirement.id] = requirement
                    logger.debug(f"Successfully parsed requirement: {requirement.id}")
                except jsonschema.exceptions.ValidationError as e:
                    logger.error(f"Skipping invalid requirement in {req_file}: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error parsing {req_file}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        if not self.requirements:
            logger.info("No valid requirements found, creating demo requirements")
            self._create_demo_requirements()
        else:
            logger.info(f"Successfully parsed {len(self.requirements)} requirements")
            logger.debug(f"Parsed requirements: {self.requirements}")
            
        return self.requirements

    def save_requirement(self, requirement: Requirement) -> Path:
        """Save a requirement to a YAML file."""
        # Create domain-based folder structure
        domain_path = requirement.domain.split('/')
        req_folder = self.requirements_dir.joinpath(*domain_path) if domain_path else self.requirements_dir
        req_folder.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save as YAML (validation happens in to_yaml())
            req_file = req_folder / f"{requirement.id.lower()}.yaml"
            req_file.write_text(requirement.to_yaml())
            logger.info(f"Saved requirement to {req_file}")
            
            # Add requirement references to implementation files
            for file_path in requirement.implementation_files:
                try:
                    self.mapper.add_requirement_reference(requirement.id, file_path)
                    logger.info(f"Added requirement reference to {file_path}")
                except Exception as e:
                    logger.error(f"Failed to add requirement reference to {file_path}: {e}")
            
            return req_file
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Failed to save requirement {requirement.id}: {e}")
            raise

    def _create_demo_requirements(self):
        """Create demo requirements if none exist."""
        demo_reqs = [
            Requirement(
                id='RQ-DEMO-001',
                domain='demo',
                description='Example requirement to demonstrate the system.',
                linked_blocks=['BLK-DEMO'],
                additional_notes=[
                    'This is a placeholder requirement',
                    'Replace with actual project requirements',
                    'Place requirements in /work/requirements'
                ],
                implementation_files=[]
            )
        ]
        
        for req in demo_reqs:
            try:
                self.save_requirement(req)
                self.requirements[req.id] = req
            except jsonschema.exceptions.ValidationError as e:
                logger.error(f"Failed to create demo requirement: {e}")
                continue