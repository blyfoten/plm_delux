"""Requirements parser for PLM system."""

import os
import logging
import frontmatter
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Requirement:
    """Requirement data model."""
    id: str
    domain: str
    description: str
    linked_blocks: List[str]
    additional_notes: List[str]
    content: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'domain': self.domain,
            'description': self.description,
            'linked_blocks': self.linked_blocks,
            'additional_notes': self.additional_notes,
            'content': self.content
        }

class RequirementsParser:
    """Parser for requirements in markdown format."""
    
    def __init__(self, workspace_dir: str = "/work"):
        """Initialize the parser with workspace directory."""
        self.workspace_dir = Path(workspace_dir)
        self.requirements_dir = self.workspace_dir / "requirements"
        self.requirements: Dict[str, Requirement] = {}
        
        # Create workspace structure if it doesn't exist
        self._ensure_workspace_structure()

    def _ensure_workspace_structure(self):
        """Ensure the workspace directory structure exists."""
        logger.info(f"Ensuring workspace structure in {self.workspace_dir}")
        
        # Create main directories
        (self.workspace_dir / "requirements").mkdir(parents=True, exist_ok=True)
        (self.workspace_dir / "generated").mkdir(parents=True, exist_ok=True)
        (self.workspace_dir / "architecture").mkdir(parents=True, exist_ok=True)

    def parse_all(self) -> Dict[str, Requirement]:
        """Parse all requirements from the workspace."""
        logger.info(f"Parsing requirements from {self.requirements_dir}")
        self.requirements.clear()
        
        if not self.requirements_dir.exists():
            logger.warning(f"Requirements directory not found: {self.requirements_dir}")
            self._create_demo_requirements()
            return self.requirements

        # Parse all .md files in subdirectories
        for req_file in self.requirements_dir.glob("**/*.md"):
            try:
                with open(req_file) as f:
                    post = frontmatter.load(f)
                    
                    # Extract metadata
                    req_id = post.get('id', '')
                    if not req_id:
                        logger.warning(f"Skipping {req_file}: No requirement ID found")
                        continue
                        
                    # Create requirement object
                    self.requirements[req_id] = Requirement(
                        id=req_id,
                        domain=post.get('domain', ''),
                        description=post.get('description', ''),
                        linked_blocks=post.get('linked_blocks', []),
                        additional_notes=self._extract_notes(post.content),
                        content=post.content
                    )
                    logger.debug(f"Parsed requirement: {req_id}")
                    
            except Exception as e:
                logger.error(f"Error parsing {req_file}: {str(e)}")
                continue
        
        if not self.requirements:
            logger.info("No requirements found, creating demo requirements")
            self._create_demo_requirements()
            
        return self.requirements

    def _extract_notes(self, content: str) -> List[str]:
        """Extract additional notes from requirement content."""
        notes = []
        in_notes = False
        
        for line in content.split('\n'):
            if '**Additional Notes:**' in line:
                in_notes = True
                continue
            elif in_notes and line.strip().startswith('-'):
                notes.append(line.strip()[1:].strip())
            elif in_notes and line.strip() and not line.strip().startswith('-'):
                in_notes = False
                
        return notes

    def validate_block_references(self, architecture_blocks: List[str]) -> List[str]:
        """Validate that all block references exist in the architecture."""
        errors = []
        for req_id, req in self.requirements.items():
            for block_id in req.linked_blocks:
                if block_id not in architecture_blocks:
                    errors.append(f"Requirement {req_id} references non-existent block {block_id}")
        return errors

    def _create_demo_requirements(self):
        """Create demo requirements if none exist."""
        demo_reqs = [
            {
                'id': 'RQ-DEMO-001',
                'domain': 'demo',
                'description': 'Example requirement to demonstrate the system.',
                'linked_blocks': ['BLK-DEMO'],
                'content': '''# Requirement RQ-DEMO-001

**Description:**  
This is an example requirement to demonstrate the system structure.

**Additional Notes:**  
- This is a placeholder requirement
- Replace with actual project requirements
- Place requirements in /work/requirements'''
            }
        ]
        
        for req in demo_reqs:
            domain_dir = self.requirements_dir / req['domain']
            domain_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = domain_dir / f"{req['id'].lower()}.md"
            with open(filepath, 'w') as f:
                f.write('---\n')
                f.write(f"id: {req['id']}\n")
                f.write(f"domain: {req['domain']}\n")
                f.write(f"linked_blocks: {req['linked_blocks']}\n")
                f.write(f"description: \"{req['description']}\"\n")
                f.write('---\n\n')
                f.write(req['content'])
            
            self.requirements[req['id']] = Requirement(
                id=req['id'],
                domain=req['domain'],
                description=req['description'],
                linked_blocks=req['linked_blocks'],
                additional_notes=self._extract_notes(req['content']),
                content=req['content']
            ) 