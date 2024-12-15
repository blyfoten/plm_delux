"""AI integration services for code analysis and generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import os
import logging
import traceback
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class GeneratedRequirement:
    """Represents a generated requirement."""
    id: str
    domain: str
    description: str
    linked_blocks: List[str]
    additional_notes: List[str]

class IAIService(ABC):
    """Interface for AI service implementations."""
    
    @abstractmethod
    async def analyze_code(self, prompt: str) -> str:
        """Analyze source code and return structured analysis."""
        pass
    
    @abstractmethod
    async def generate_requirements(self, domain: str, context: str) -> List[GeneratedRequirement]:
        """Generate requirements based on domain and context."""
        pass
    
    @abstractmethod
    async def determine_domain(self, file_content: str, available_domains: List[str]) -> Optional[str]:
        """Determine the most appropriate domain for a file based on its content."""
        pass

    @abstractmethod
    async def recommend_domains(self, context: str) -> Dict[str, Any]:
        """Generate domain recommendations based on code analysis."""
        pass

class OpenAIService(IAIService):
    """Service for interacting with OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI service."""
        logger.info("Initializing OpenAI service")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("No OpenAI API key provided")
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.debug("OpenAI client initialized")

    async def _get_completion(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.2) -> str:
        """Get completion from OpenAI."""
        try:
            logger.debug(f"Sending completion request to OpenAI (max_tokens={max_tokens}, temp={temperature})")
            logger.debug(f"Prompt preview: {prompt[:200]}...")
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are a code analysis assistant. Provide clear, structured responses."
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                response_format={
                    "type": "text"
                },
                temperature=temperature,
                max_completion_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            logger.debug("Received completion from OpenAI")
            result = response.choices[0].message.content
            logger.debug(f"Response preview: {result[:200]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error getting completion from OpenAI: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def analyze_code(self, prompt: str) -> str:
        """Analyze code using OpenAI."""
        try:
            logger.debug("Sending code analysis request to OpenAI")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            return await self._get_completion(
                prompt,
                max_tokens=2000,
                temperature=0.2
            )
            
        except Exception as e:
            logger.error(f"Error analyzing code with OpenAI: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _mock_analysis(self) -> str:
        """Return mock analysis when OpenAI is not available."""
        logger.info("Generating mock analysis")
        return """This appears to be a utility module.

- Provides helper functions
- Handles data processing
- Contains utility classes

Dependencies on standard library modules
Basic file I/O operations
Common string manipulation

Simple implementation with standard patterns
Follows common Python conventions

No major issues identified
Consider adding more documentation"""

    async def generate_requirements(self, domain: str, context: str) -> List[GeneratedRequirement]:
        """Generate requirements based on domain and context."""
        try:
            logger.info(f"Generating requirements for domain: {domain}")
            logger.debug(f"Context preview: {context[:200]}...")
            
            prompt = f"""Based on the following code analysis context, generate requirements for the {domain} domain.
Format each requirement exactly as follows (no markdown headers):

RQ-{domain.upper()}-XXX (where XXX is a sequential number)
Description: (clear, concise requirement statement)
Additional Notes:
- (implementation consideration 1)
- (implementation consideration 2)
Linked Blocks:
- (architectural component 1)
- (architectural component 2)

Generate 5-8 well-defined requirements that cover the key functionality and characteristics shown in the context.
Focus on both functional and non-functional requirements.
Make sure each requirement is specific, measurable, and testable.

Context:
{context}"""

            response = await self._get_completion(prompt, max_tokens=2000, temperature=0.7)
            logger.debug(f"Generated requirements response: {response[:200]}...")
            logger.debug("Full response for debugging:")
            logger.debug(response)
            
            # Parse the response into requirements
            requirements = []
            current_req = None
            
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                # Remove any markdown formatting
                line = line.replace('###', '').strip()
                
                if 'RQ-' in line:
                    # If we have a previous requirement, add it to the list
                    if current_req:
                        logger.debug(f"Adding requirement: {current_req.id}")
                        requirements.append(current_req)
                    
                    # Extract the requirement ID (everything up to the first space)
                    req_id = line.split()[0] if ' ' in line else line
                    logger.debug(f"Found requirement ID: {req_id}")
                    
                    current_req = GeneratedRequirement(
                        id=req_id,
                        domain=domain,
                        description="",
                        linked_blocks=[],
                        additional_notes=[]
                    )
                elif current_req:
                    if line.startswith('Description:'):
                        current_req.description = line.replace('Description:', '').strip()
                        logger.debug(f"Added description: {current_req.description[:50]}...")
                    elif line.startswith('Additional Notes:'):
                        continue
                    elif line.startswith('Linked Blocks:'):
                        continue
                    elif line.startswith('-'):
                        item = line[1:].strip()
                        # Look at the previous non-empty line to determine the section
                        prev_line = next((l for l in reversed(lines[:i]) if l), '')
                        if 'Additional Notes:' in prev_line or (current_req.additional_notes and not current_req.linked_blocks):
                            current_req.additional_notes.append(item)
                            logger.debug(f"Added note: {item}")
                        elif 'Linked Blocks:' in prev_line or current_req.linked_blocks:
                            current_req.linked_blocks.append(item)
                            logger.debug(f"Added linked block: {item}")

            # Add the last requirement if there is one
            if current_req:
                logger.debug(f"Adding final requirement: {current_req.id}")
                requirements.append(current_req)
            
            logger.info(f"Successfully parsed {len(requirements)} requirements")
            for req in requirements:
                logger.debug(f"Requirement {req.id}:")
                logger.debug(f"  Description: {req.description[:50]}...")
                logger.debug(f"  Notes: {len(req.additional_notes)} notes")
                logger.debug(f"  Blocks: {len(req.linked_blocks)} blocks")
            
            return requirements
            
        except Exception as e:
            logger.error(f"Error generating requirements: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def determine_domain(self, file_content: str, available_domains: List[str]) -> Optional[str]:
        """Determine the most appropriate domain for a file based on its content."""
        try:
            logger.info("Determining domain for file content")
            logger.debug(f"Available domains: {available_domains}")
            logger.debug(f"Content preview: {file_content[:200]}...")
            
            if not available_domains:
                logger.warning("No available domains provided")
                return None
                
            prompt = f"""Based on this source code, determine which domain it belongs to.
Available domains: {', '.join(available_domains)}

Source code:
{file_content}

Reply with just the domain name, nothing else."""

            response = await self._get_completion(prompt, max_tokens=50, temperature=0.3)
            domain = response.strip()
            
            if domain in available_domains:
                logger.info(f"Determined domain: {domain}")
                return domain
            else:
                logger.warning(f"Determined domain '{domain}' not in available domains")
                return None
                
        except Exception as e:
            logger.error(f"Error determining domain: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def recommend_domains(self, context: str) -> Dict[str, Any]:
        """Generate domain recommendations based on code analysis."""
        try:
            prompt = f"""Based on the following code analysis context, recommend an optimal domain structure.
For each recommended domain:
1. Suggest a clear domain_id (lowercase, underscores)
2. Provide a descriptive name
3. Write a brief description of the domain's purpose
4. List any logical subdomains (if applicable)
5. Include a confidence score (0.0 to 1.0) for this recommendation
6. Provide reasoning for this recommendation

Context:
{context}

Respond in the following JSON format:
{{
    "recommendations": [
        {{
            "domain_id": "example_domain",
            "name": "Example Domain",
            "description": "Description of the domain",
            "subdomain_ids": ["sub1", "sub2"],
            "confidence": 0.85,
            "reasoning": "Explanation for this recommendation"
        }}
    ],
    "changes_detected": true
}}

Focus on creating a clean, logical separation of concerns. Consider:
- Code dependencies and coupling
- Functional relationships
- Data flow patterns
- Common architectural patterns
- Current domain assignments (if any)
"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a software architecture expert specializing in domain-driven design."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            recommendations = json.loads(response.choices[0].message.content)
            return recommendations

        except Exception as e:
            logger.error(f"Error generating domain recommendations: {e}")
            raise

class MockAIService(IAIService):
    """Mock implementation of the AI service for testing."""

    async def analyze_code(self, prompt: str) -> str:
        """Return mock analysis."""
        return """Primary purpose
This is a mock analysis.

Key functionality
- Mock function 1
- Mock function 2

Dependencies and interfaces
- Mock dependency 1
- Mock interface 1

Important implementation details
- Mock detail 1
- Mock detail 2

Potential issues
- Mock issue 1"""

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

    async def determine_domain(self, file_content: str, available_domains: List[str]) -> Optional[str]:
        """Return mock domain."""
        return available_domains[0] if available_domains else None 

    async def recommend_domains(self, context: str) -> Dict[str, Any]:
        """Return mock domain recommendations."""
        return {
            "recommendations": [
                {
                    "domain_id": "mock_domain",
                    "name": "Mock Domain",
                    "description": "A mock domain for testing",
                    "subdomain_ids": ["mock_sub1", "mock_sub2"],
                    "confidence": 0.9,
                    "reasoning": "This is a mock recommendation for testing purposes"
                }
            ],
            "changes_detected": True
        }