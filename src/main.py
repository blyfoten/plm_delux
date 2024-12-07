import os
import logging
from architecture import system_architecture
from requirements_parser import RequirementsParser
from code_generator import CodeGenerator
from visualizer import ArchitectureVisualizer

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize the requirements parser
    logger.info("Parsing requirements...")
    parser = RequirementsParser("requirements")
    requirements = parser.parse_all()
    logger.info(f"Found {len(requirements)} requirements")

    # Get all block IDs from the system architecture
    block_ids = [system_architecture.block_id]
    for block in system_architecture.subblocks:
        block_ids.append(block.block_id)
    logger.info(f"Found {len(block_ids)} architecture blocks")

    # Validate block references
    errors = parser.validate_block_references(block_ids)
    if errors:
        logger.error("Validation errors found:")
        for error in errors:
            logger.error(f"- {error}")
        return

    # Generate code
    logger.info("Generating code stubs...")
    generator = CodeGenerator("src/generated", requirements)
    generator.generate_all(system_architecture)
    logger.info("Code generation complete!")

    # Generate architecture diagram
    logger.info("Generating architecture diagram...")
    visualizer = ArchitectureVisualizer(requirements)
    visualizer.generate_diagram(system_architecture, "docs/architecture")
    logger.info("Architecture visualization complete!")

if __name__ == "__main__":
    main() 