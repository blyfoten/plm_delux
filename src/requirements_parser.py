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
        self.requirements = {}  # Clear existing requirements
        
        if not os.path.exists(self.requirements_dir):
            os.makedirs(self.requirements_dir)
            # Create demo requirements if directory is empty
            self._create_demo_requirements()
        
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

    def _create_demo_requirements(self):
        """Create demo requirements if none exist."""
        demo_reqs = [
            {
                'id': 'RQ-UI-001',
                'domain': 'ui',
                'description': 'Elevator shall have UI with floor buttons and a real-time display.',
                'linked_blocks': ['BLK-UI-DISPLAY', 'BLK-UI-BUTTONS'],
                'content': '''# Requirement RQ-UI-001

**Description:**  
The elevator shall include physical buttons for selecting floors and an accompanying digital display that shows the current floor and direction of travel.

**Additional Notes:**  
- The display updates in real-time.
- The number of buttons depends on the number of floors.
- The display should show:
  - Current floor number
  - Direction of travel (up/down)
  - Status messages (e.g., "Door Opening", "Door Closing")'''
            },
            {
                'id': 'RQ-UI-002',
                'domain': 'ui',
                'description': 'Elevator shall have an alarm system with audio and visual indicators.',
                'linked_blocks': ['BLK-UI-ALARM', 'BLK-ALARM-COMM'],
                'content': '''# Requirement RQ-UI-002

**Description:**  
The elevator shall include an alarm system that provides both audio and visual indicators for emergency situations.

**Additional Notes:**  
- Audio alarm with configurable volume
- Visual strobe light for hearing-impaired users
- Emergency button with tactile feedback
- Direct communication link to building security
- Battery backup for alarm system'''
            },
            {
                'id': 'RQ-MD-001',
                'domain': 'motor_and_doors',
                'description': 'Elevator motor control system for vertical movement',
                'linked_blocks': ['BLK-MOTOR'],
                'content': '''# Requirement RQ-MD-001

**Description:**  
The elevator motor control system shall provide precise control of vertical movement between floors, including acceleration and deceleration profiles for passenger comfort.

**Additional Notes:**  
- Support variable speed control
- Implement smooth acceleration and deceleration
- Include emergency stop capability
- Monitor motor temperature and current draw
- Support both up and down movement
- Implement position feedback for accurate floor leveling'''
            },
            {
                'id': 'RQ-MD-002',
                'domain': 'motor_and_doors',
                'description': 'Automatic door control system with safety features',
                'linked_blocks': ['BLK-DOOR'],
                'content': '''# Requirement RQ-MD-002

**Description:**  
The door control system shall provide smooth and safe operation of the elevator doors with obstacle detection.

**Additional Notes:**  
- Obstacle detection and auto-reverse
- Adjustable door timing
- Emergency manual operation
- Door position monitoring
- Energy-efficient operation
- Sound indication during door movement'''
            },
            {
                'id': 'RQ-SYS-001',
                'domain': 'system',
                'description': 'Over-the-air (OTA) update capability for all subsystems',
                'linked_blocks': ['BLK-OTA'],
                'content': '''# Requirement RQ-SYS-001

**Description:**  
The system shall support secure over-the-air updates for all software components with rollback capability.

**Additional Notes:**  
- Secure update mechanism
- Version control and rollback
- Update progress monitoring
- Automatic integrity verification
- Scheduled update windows
- Minimal downtime during updates'''
            }
        ]
        
        for req in demo_reqs:
            domain_dir = os.path.join(self.requirements_dir, req['domain'])
            os.makedirs(domain_dir, exist_ok=True)
            
            filepath = os.path.join(domain_dir, f"{req['id'].lower()}.md")
            with open(filepath, 'w') as f:
                f.write('---\n')
                f.write(f"id: {req['id']}\n")
                f.write(f"domain: {req['domain']}\n")
                f.write(f"linked_blocks: {req['linked_blocks']}\n")
                f.write(f"description: \"{req['description']}\"\n")
                f.write('---\n\n')
                f.write(req['content'])