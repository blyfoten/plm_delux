import os
from typing import Dict, List, Optional
import openai
from dataclasses import dataclass

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
    description: str
    requirements: List[str]

class AIIntegrator:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI integrator with OpenAI API key."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        openai.api_key = self.api_key

    async def generate_requirements(self, domain: str, context: str) -> List[GeneratedRequirement]:
        """Generate requirements for a given domain based on context."""
        prompt = f"""Generate requirements for an elevator control system's {domain} domain.
        Context: {context}
        
        Format each requirement as:
        - ID (e.g., RQ-{domain.upper()}-XXX)
        - Description
        - Linked architectural blocks
        - Additional implementation notes
        
        Focus on specific, testable requirements that can be implemented in code."""

        response = await openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a requirements engineering expert specializing in elevator control systems."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        # Parse the response and convert to GeneratedRequirement objects
        requirements = self._parse_requirements_response(response.choices[0].message.content, domain)
        return requirements

    async def generate_code(self, requirement: GeneratedRequirement) -> GeneratedCode:
        """Generate code implementation for a given requirement."""
        prompt = f"""Generate Python code to implement the following requirement:
        
        Requirement ID: {requirement.id}
        Description: {requirement.description}
        Additional Notes:
        {chr(10).join(f'- {note}' for note in requirement.additional_notes)}
        
        Generate production-quality Python code with:
        - Proper type hints
        - Comprehensive docstrings
        - Error handling
        - Logging
        - Unit test placeholders"""

        response = await openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Python developer specializing in elevator control systems."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        return GeneratedCode(
            block_id=requirement.linked_blocks[0],
            code=response.choices[0].message.content,
            description=requirement.description,
            requirements=[requirement.id]
        )

    def _parse_requirements_response(self, response: str, domain: str) -> List[GeneratedRequirement]:
        """Parse the AI response into structured requirement objects."""
        requirements = []
        current_req = None
        current_section = None

        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith('RQ-') or line.startswith('- RQ-'):
                # Save previous requirement if exists
                if current_req:
                    requirements.append(current_req)
                
                # Start new requirement
                req_id = line.replace('- ', '')
                current_req = GeneratedRequirement(
                    id=req_id,
                    domain=domain,
                    description="",
                    linked_blocks=[],
                    additional_notes=[]
                )
                current_section = "id"
            
            elif line.lower().startswith('description:'):
                current_req.description = line.split(':', 1)[1].strip()
                current_section = "description"
            
            elif line.lower().startswith('linked blocks:'):
                blocks = line.split(':', 1)[1].strip()
                current_req.linked_blocks = [b.strip() for b in blocks.split(',')]
                current_section = "blocks"
            
            elif line.lower().startswith('additional notes:'):
                current_section = "notes"
            
            elif line.startswith('- ') and current_section == "notes":
                current_req.additional_notes.append(line[2:])

        # Add the last requirement
        if current_req:
            requirements.append(current_req)

        return requirements

    async def enhance_code_with_tests(self, code: GeneratedCode) -> GeneratedCode:
        """Enhance generated code with unit tests."""
        prompt = f"""Given the following code implementation:

        {code.code}

        Generate comprehensive unit tests that:
        1. Test all public methods
        2. Include edge cases
        3. Mock external dependencies
        4. Follow pytest best practices"""

        response = await openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in Python testing and test-driven development."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        # Append the tests to the original code
        code.code += "\n\n# Unit Tests\n" + response.choices[0].message.content
        return code

    async def suggest_architecture_improvements(self, current_architecture: str) -> str:
        """Suggest improvements to the current architecture."""
        prompt = f"""Review the current architecture and suggest improvements:

        Current Architecture:
        {current_architecture}

        Consider:
        1. Modularity and coupling
        2. Scalability
        3. Maintainability
        4. Security
        5. Performance
        
        Provide specific, actionable suggestions."""

        response = await openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a software architect specializing in elevator control systems."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content 