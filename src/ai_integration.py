"""AI integration services and interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import os
import logging
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI service with API key."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        openai.api_key = self.api_key
        logger.info("OpenAIService initialized")

    async def _get_completion(self, prompt: str, max_tokens: int = 2000) -> str:
        """Get completion from OpenAI API."""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant specializing in software engineering, requirements analysis, and code generation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=1.0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error getting completion from OpenAI: {str(e)}")
            raise

    async def generate_requirements(self, domain: str, context: str) -> List[GeneratedRequirement]:
        """Generate requirements based on domain and context."""
        logger.info(f"Generating requirements for domain: {domain}")
        
        # Load the requirements prompt template
        prompt_path = Path(__file__).parent / "prompts" / "generate_requirements.txt"
        with open(prompt_path) as f:
            prompt_template = f.read()

        # Format the prompt
        prompt = prompt_template.format(
            domain=domain,
            context=context
        )

        try:
            # Get completion from OpenAI
            response = await self._get_completion(prompt)
            
            # Parse the response into requirements
            requirements = []
            current_req = None
            
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('REQ-'):
                    if current_req:
                        requirements.append(current_req)
                    
                    # Parse requirement ID and description
                    parts = line.split(':', 1)
                    req_id = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ""
                    
                    current_req = GeneratedRequirement(
                        id=req_id,
                        domain=domain,
                        description=description,
                        linked_blocks=[],  # Will be filled based on notes
                        additional_notes=[]
                    )
                elif line.startswith('-') and current_req:
                    note = line[1:].strip()
                    current_req.additional_notes.append(note)
                    # Try to extract block references from notes
                    if 'BLK-' in note:
                        blocks = [word for word in note.split() if word.startswith('BLK-')]
                        current_req.linked_blocks.extend(blocks)

            if current_req:
                requirements.append(current_req)

            logger.info(f"Generated {len(requirements)} requirements")
            return requirements

        except Exception as e:
            logger.error(f"Error generating requirements: {str(e)}")
            raise

    async def generate_code(self, requirement: dict) -> GeneratedCode:
        """Generate code implementation for a requirement."""
        logger.info(f"Generating code for requirement: {requirement['id']}")
        
        # Load the code generation prompt template
        prompt_path = Path(__file__).parent / "prompts" / "generate_code.txt"
        with open(prompt_path) as f:
            prompt_template = f.read()

        # Format the prompt
        notes = "\n".join(f"- {note}" for note in requirement.get('additional_notes', []))
        prompt = prompt_template.format(
            requirement=requirement,
            notes=notes
        )

        try:
            # Get completion from OpenAI
            response = await self._get_completion(prompt, max_tokens=3000)
            
            # Extract the block ID from linked blocks
            block_id = requirement['linked_blocks'][0] if requirement['linked_blocks'] else "BLK-UNKNOWN"
            
            return GeneratedCode(
                block_id=block_id,
                code=response
            )

        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise

    async def enhance_code_with_tests(self, generated: GeneratedCode) -> GeneratedCode:
        """Add tests to generated code."""
        logger.info(f"Enhancing code with tests for block: {generated.block_id}")
        
        prompt = f"""
Given the following Python code, generate comprehensive unit tests:

{generated.code}

Generate pytest-based unit tests that:
1. Test all public methods and functions
2. Include edge cases and error conditions
3. Use appropriate fixtures and mocks
4. Follow testing best practices
5. Include docstrings and comments
"""

        try:
            # Get completion from OpenAI
            tests = await self._get_completion(prompt, max_tokens=2000)
            
            # Return enhanced code with tests
            return GeneratedCode(
                block_id=generated.block_id,
                code=generated.code,
                tests=tests
            )

        except Exception as e:
            logger.error(f"Error enhancing code with tests: {str(e)}")
            raise

    async def suggest_architecture_improvements(self, current_architecture: str) -> str:
        """Suggest improvements to the current architecture."""
        logger.info("Generating architecture improvement suggestions")
        
        prompt = f"""
Analyze the following system architecture and suggest improvements:

{current_architecture}

Consider:
1. Modularity and coupling
2. SOLID principles
3. Scalability and maintainability
4. Error handling and reliability
5. Performance optimization opportunities

Provide specific, actionable suggestions with examples.
"""

        try:
            return await self._get_completion(prompt)
        except Exception as e:
            logger.error(f"Error suggesting architecture improvements: {str(e)}")
            raise

class MockAIService(IAIService):
    """Mock implementation of the AI service for testing."""

    async def generate_requirements(self, domain: str, context: str) -> List[GeneratedRequirement]:
        """Generate mock requirements."""
        return [
            GeneratedRequirement(
                id=f"RQ-{domain.upper()}-001",
                domain=domain,
                description="Mock requirement for testing",
                linked_blocks=["BLK-TEST"],
                additional_notes=["Mock note 1", "Mock note 2"]
            )
        ]

    async def generate_code(self, requirement: dict) -> GeneratedCode:
        """Generate mock code."""
        return GeneratedCode(
            block_id="BLK-TEST",
            code="def mock_function():\n    pass"
        )

    async def enhance_code_with_tests(self, generated: GeneratedCode) -> GeneratedCode:
        """Add mock tests."""
        generated.tests = "def test_mock():\n    assert True"
        return generated

    async def suggest_architecture_improvements(self, current_architecture: str) -> str:
        """Suggest mock improvements."""
        return "Mock architecture improvement suggestion" 