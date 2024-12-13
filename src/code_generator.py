"""Code generation utilities."""

import os
from typing import Dict
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from .requirements_parser import Requirement
from .architecture import Block

class CodeGenerator:
    def __init__(self, settings: dict, requirements: Dict[str, Requirement]):
        """Initialize code generator with settings and requirements."""
        self.settings = settings
        self.requirements = requirements
        self.output_dir = str(Path(os.getenv("WORKSPACE_DIR", "/work")) / settings["source_folder"])

    def generate_block_code(self, block: Block) -> None:
        """Generate code stubs for a given architecture block."""
        # Create module directory if it doesn't exist
        module_dir = os.path.join(self.output_dir, block.block_id.lower())
        os.makedirs(module_dir, exist_ok=True)

        # Generate main module file
        module_file = os.path.join(module_dir, "__init__.py")
        with open(module_file, "w") as f:
            f.write(self._generate_module_header(block))
            f.write("\n\n")
            f.write(self._generate_imports())
            f.write("\n\n")
            f.write(self._generate_class_definition(block))
            f.write("\n\n")
            f.write(self._generate_function_prototypes(block))

    def _generate_module_header(self, block: Block) -> str:
        """Generate module header with documentation."""
        header = f'"""\n{block.name} ({block.block_id})\n\n'
        header += "Requirements implemented:\n"
        for req_id in block.requirements:
            if req_id in self.requirements:
                req = self.requirements[req_id]
                header += f"- {req_id}: {req.description}\n"
        header += '"""\n'
        return header

    def _generate_imports(self) -> str:
        """Generate required import statements."""
        imports = [
            "from typing import Optional, List, Dict",
            "from dataclasses import dataclass",
            "from enum import Enum, auto"
        ]
        return "\n".join(imports)

    def _generate_class_definition(self, block: Block) -> str:
        """Generate the main class definition for the block."""
        class_name = "".join(word.capitalize() for word in block.name.split())
        
        # Generate enums and dataclasses based on block type
        class_def = ""
        if "UI" in block.block_id:
            class_def += "class DisplayState(Enum):\n"
            class_def += "    IDLE = auto()\n"
            class_def += "    MOVING_UP = auto()\n"
            class_def += "    MOVING_DOWN = auto()\n"
            class_def += "    DOOR_OPENING = auto()\n"
            class_def += "    DOOR_CLOSING = auto()\n\n"
        elif "MOTOR" in block.block_id:
            class_def += "@dataclass\n"
            class_def += "class MotorStatus:\n"
            class_def += "    temperature: float\n"
            class_def += "    current_draw: float\n"
            class_def += "    speed: float\n"
            class_def += "    position: float\n\n"

        # Main class definition
        class_def += f"class {class_name}:\n"
        class_def += "    def __init__(self):\n"
        
        # Add attributes based on block type
        if "UI" in block.block_id:
            class_def += "        self.current_floor: int = 1\n"
            class_def += "        self.state: DisplayState = DisplayState.IDLE\n"
        elif "MOTOR" in block.block_id:
            class_def += "        self.status: MotorStatus = MotorStatus(\n"
            class_def += "            temperature=0.0,\n"
            class_def += "            current_draw=0.0,\n"
            class_def += "            speed=0.0,\n"
            class_def += "            position=0.0\n"
            class_def += "        )\n"
        else:
            class_def += "        pass\n"
        
        return class_def

    def _generate_function_prototypes(self, block: Block) -> str:
        """Generate detailed function prototypes based on requirements."""
        prototypes = []
        for req_id in block.requirements:
            if req_id not in self.requirements:
                continue
                
            req = self.requirements[req_id]
            func_name = f"handle_{req_id.lower().replace('-', '_')}"
            
            # Generate function with appropriate parameters and docstring
            if "MOTOR" in block.block_id:
                proto = f"def {func_name}(self, target_floor: int, speed: float = 1.0) -> bool:\n"
                proto += f'    """{req.description}\n\n'
                proto += "    Args:\n"
                proto += "        target_floor: The floor to move to\n"
                proto += "        speed: Movement speed factor (0.0 to 1.0)\n\n"
                proto += "    Returns:\n"
                proto += "        bool: True if movement completed successfully\n"
                proto += '    """\n'
                proto += "    # TODO: Implement motor control logic\n"
                proto += "    # - Check current position\n"
                proto += "    # - Calculate direction and distance\n"
                proto += "    # - Apply acceleration profile\n"
                proto += "    # - Monitor temperature and current\n"
                proto += "    # - Update position feedback\n"
                proto += "    return True\n"
            
            elif "UI" in block.block_id:
                proto = f"def {func_name}(self, message: str = None) -> None:\n"
                proto += f'    """{req.description}\n\n'
                proto += "    Args:\n"
                proto += "        message: Optional status message to display\n"
                proto += '    """\n'
                proto += "    # TODO: Implement UI update logic\n"
                proto += "    # - Update floor number\n"
                proto += "    # - Update direction indicator\n"
                proto += "    # - Show status message if provided\n"
                proto += "    pass\n"
            
            else:
                proto = f"def {func_name}(self):\n"
                proto += f'    """{req.description}\n'
                proto += '    """\n'
                proto += f"    # TODO: implement {req_id}\n"
                proto += "    pass\n"
            
            prototypes.append(proto)
        
        return "\n\n".join(prototypes)

    def generate_all(self, system_architecture: Block) -> None:
        """Generate code for the entire system architecture."""
        self.generate_block_code(system_architecture)
        for subblock in system_architecture.subblocks:
            self.generate_block_code(subblock) 