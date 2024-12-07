import os
import yaml
import frontmatter
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Requirement:
    id: str
    domain: str
    linked_blocks: List[str]
    description: str
    content: str

class RequirementsParser:
    def __init__(self, requirements_dir: str):
        self.requirements_dir = requirements_dir
        self.requirements: Dict[str, Requirement] = {}

    def parse_all(self) -> Dict[str, Requirement]:
        """Parse all requirement files in the requirements directory and its subdirectories."""
        for root, _, files in os.walk(self.requirements_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    self._parse_file(file_path)
        return self.requirements

    def _parse_file(self, file_path: str) -> None:
        """Parse a single requirement file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            
            # Validate required fields
            required_fields = ['id', 'domain', 'linked_blocks', 'description']
            for field in required_fields:
                if field not in post.metadata:
                    raise ValueError(f"Missing required field '{field}' in {file_path}")

            req = Requirement(
                id=post.metadata['id'],
                domain=post.metadata['domain'],
                linked_blocks=post.metadata['linked_blocks'],
                description=post.metadata['description'],
                content=post.content
            )
            self.requirements[req.id] = req

    def validate_block_references(self, architecture_blocks: List[str]) -> List[str]:
        """Validate that all block references exist in the architecture."""
        errors = []
        for req_id, req in self.requirements.items():
            for block_id in req.linked_blocks:
                if block_id not in architecture_blocks:
                    errors.append(f"Requirement {req_id} references non-existent block {block_id}")
        return errors 