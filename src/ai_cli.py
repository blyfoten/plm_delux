import asyncio
import click
import os
from typing import Optional
from ai_integration import AIIntegrator
from requirements_parser import RequirementsParser
from code_generator import CodeGenerator
from visualizer import ArchitectureVisualizer
from architecture import system_architecture

@click.group()
def cli():
    """PLM AI CLI - Generate and manage requirements, code, and architecture."""
    pass

@cli.command()
@click.option('--domain', '-d', required=True, help='Domain to generate requirements for (e.g., ui, motor_and_doors)')
@click.option('--context', '-c', required=True, help='Context description for requirement generation')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
async def generate_requirements(domain: str, context: str, api_key: Optional[str]):
    """Generate new requirements for a specified domain."""
    ai = AIIntegrator(api_key)
    requirements = await ai.generate_requirements(domain, context)
    
    # Create requirements directory if it doesn't exist
    domain_dir = os.path.join('requirements', domain)
    os.makedirs(domain_dir, exist_ok=True)
    
    # Save each requirement as a markdown file
    for req in requirements:
        filename = f"{req.id.lower()}.md"
        filepath = os.path.join(domain_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write('---\n')
            f.write(f'id: {req.id}\n')
            f.write(f'domain: {req.domain}\n')
            f.write(f'linked_blocks: {req.linked_blocks}\n')
            f.write(f'description: "{req.description}"\n')
            f.write('---\n\n')
            f.write(f'# Requirement {req.id}\n\n')
            f.write('**Description:**  \n')
            f.write(f'{req.description}\n\n')
            f.write('**Additional Notes:**  \n')
            for note in req.additional_notes:
                f.write(f'- {note}\n')
    
    click.echo(f"Generated {len(requirements)} requirements in {domain_dir}")

@cli.command()
@click.option('--requirement-id', '-r', required=True, help='ID of the requirement to implement')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
async def generate_code(requirement_id: str, api_key: Optional[str]):
    """Generate code implementation for a requirement."""
    # Parse existing requirements
    parser = RequirementsParser("requirements")
    requirements = parser.parse_all()
    
    if requirement_id not in requirements:
        click.echo(f"Error: Requirement {requirement_id} not found")
        return
    
    # Generate code
    ai = AIIntegrator(api_key)
    requirement = requirements[requirement_id]
    generated = await ai.generate_code(requirement)
    
    # Add tests
    generated = await ai.enhance_code_with_tests(generated)
    
    # Save the generated code
    output_dir = os.path.join('src', 'generated', generated.block_id.lower())
    os.makedirs(output_dir, exist_ok=True)
    
    impl_file = os.path.join(output_dir, 'implementation.py')
    with open(impl_file, 'w') as f:
        f.write(generated.code)
    
    click.echo(f"Generated code in {impl_file}")

@cli.command()
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
async def improve_architecture(api_key: Optional[str]):
    """Get AI suggestions for improving the architecture."""
    # Get current architecture as string representation
    current_arch = str(system_architecture)
    
    # Get improvement suggestions
    ai = AIIntegrator(api_key)
    suggestions = await ai.suggest_architecture_improvements(current_arch)
    
    # Save suggestions to a file
    with open('docs/architecture_suggestions.md', 'w') as f:
        f.write('# Architecture Improvement Suggestions\n\n')
        f.write(suggestions)
    
    click.echo("Architecture suggestions saved to docs/architecture_suggestions.md")

@cli.command()
def visualize():
    """Generate visual representation of the current architecture."""
    # Parse requirements
    parser = RequirementsParser("requirements")
    requirements = parser.parse_all()
    
    # Generate visualization
    visualizer = ArchitectureVisualizer(requirements)
    visualizer.generate_diagram(system_architecture, "docs/architecture")
    
    click.echo("Architecture diagram generated in docs/architecture.png")

def main():
    """Entry point for the CLI application."""
    # Create an event loop and run the async commands
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(cli())
    finally:
        loop.close()

if __name__ == '__main__':
    main() 