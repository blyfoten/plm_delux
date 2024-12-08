"""AI integration services and interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import os

@dataclass
class GeneratedRequirement:
    id: str
    domain: str
    description: str
    linked_blocks: List[str]
    additional_notes: List[str]

@dataclass
class GeneratedCode:
    block_id: str
    code: str
    tests: Optional[str] = None

class IAIService(ABC):
    """Interface for AI service implementations."""
    
    @abstractmethod
    async def generate_requirements(self, domain: str, context: str) -> List[GeneratedRequirement]:
        """Generate requirements based on domain and context."""
        pass
    
    @abstractmethod
    async def generate_code(self, requirement: dict) -> GeneratedCode:
        """Generate code implementation for a requirement."""
        pass
    
    @abstractmethod
    async def enhance_code_with_tests(self, generated: GeneratedCode) -> GeneratedCode:
        """Add tests to generated code."""
        pass
    
    @abstractmethod
    async def suggest_architecture_improvements(self, current_architecture: str) -> str:
        """Suggest improvements to the current architecture."""
        pass

class OpenAIService(IAIService):
    """OpenAI-based implementation of the AI service."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompt templates from files."""
        prompts_dir = Path(__file__).parent / "prompts"
        self.prompts = {}
        for prompt_file in prompts_dir.glob("*.txt"):
            self.prompts[prompt_file.stem] = prompt_file.read_text()
    
    async def generate_requirements(self, domain: str, context: str) -> List[GeneratedRequirement]:
        # Implementation using OpenAI API
        pass
    
    async def generate_code(self, requirement: dict) -> GeneratedCode:
        # Implementation using OpenAI API
        pass
    
    async def enhance_code_with_tests(self, generated: GeneratedCode) -> GeneratedCode:
        # Implementation using OpenAI API
        pass
    
    async def suggest_architecture_improvements(self, current_architecture: str) -> str:
        # Implementation using OpenAI API
        pass

class MockAIService(IAIService):
    """Mock implementation for testing."""
    
    async def generate_requirements(self, domain: str, context: str) -> List[GeneratedRequirement]:
        return [
            GeneratedRequirement(
                id=f"RQ-{domain.upper()}-001",
                domain=domain,
                description="Mock requirement for testing",
                linked_blocks=[],
                additional_notes=["Test note"]
            )
        ]
    
    async def generate_code(self, requirement: dict) -> GeneratedCode:
        return GeneratedCode(
            block_id="TEST-BLOCK",
            code="def test(): pass",
            tests="def test_function(): assert True"
        )
    
    async def enhance_code_with_tests(self, generated: GeneratedCode) -> GeneratedCode:
        return generated
    
    async def suggest_architecture_improvements(self, current_architecture: str) -> str:
        return "Mock architecture improvement suggestion" 