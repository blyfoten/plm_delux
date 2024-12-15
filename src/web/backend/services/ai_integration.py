"""AI integration services for code analysis and generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import os
import logging
import traceback
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
Format each requirement as:
- ID (format: RQ-{domain.upper()}-XXX where XXX is a number)
- Description (clear, concise requirement statement)
- Additional notes (implementation considerations)
- Suggested linked blocks (architectural components that should implement this)

Context:
{context}

Generate 3-5 well-defined requirements."""

            response = await self._get_completion(prompt, max_tokens=2000, temperature=0.7)
            logger.debug(f"Generated requirements response: {response[:200]}...")
            
            # Parse the response into requirements
            requirements = []
            current_req = None
            
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('RQ-'):
                    if current_req:
                        requirements.append(current_req)
                    current_req = GeneratedRequirement(
                        id=line,
                        domain=domain,
                        description="",
                        linked_blocks=[],
                        additional_notes=[]
                    )
                elif current_req:
                    if line.startswith('- Description:'):
                        current_req.description = line.replace('- Description:', '').strip()
                    elif line.startswith('- Additional notes:'):
                        current_req.additional_notes.append(line.replace('- Additional notes:', '').strip())
                    elif line.startswith('- Linked blocks:'):
                        blocks = line.replace('- Linked blocks:', '').strip()
                        current_req.linked_blocks = [b.strip() for b in blocks.split(',')]

            if current_req:
                requirements.append(current_req)
            
            logger.info(f"Generated {len(requirements)} requirements")
            logger.debug(f"Requirements: {requirements}")
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