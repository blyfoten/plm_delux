"""Architecture visualization service."""

from typing import Dict
import graphviz
from .architecture import Block
from .requirements_parser import Requirement

class ArchitectureVisualizer:
    def __init__(self, requirements: Dict[str, Requirement]):
        self.requirements = requirements

    def generate_diagram(self, system_architecture: Block, output_file: str) -> None:
        """Generate a system architecture diagram using Graphviz."""
        dot = graphviz.Digraph(comment='System Architecture')
        dot.attr(rankdir='TB')  # Top to bottom layout
        
        # Set default node attributes
        dot.attr('node', shape='box', style='rounded')
        
        # Add system block
        dot.node(system_architecture.block_id, 
                self._format_node_label(system_architecture),
                style='filled', fillcolor='lightblue')

        # Add all subblocks
        for block in system_architecture.subblocks:
            # Set color based on domain
            color = self._get_domain_color(block)
            dot.node(block.block_id, 
                    self._format_node_label(block),
                    style='filled', fillcolor=color)
            
            # Connect to system block
            dot.edge(system_architecture.block_id, block.block_id)

        # Add requirement connections
        self._add_requirement_connections(dot, system_architecture)

        # Save the diagram
        dot.render(output_file, view=True, format='png')

    def _format_node_label(self, block: Block) -> str:
        """Format the node label with block details."""
        label = f"{block.name}\\n({block.block_id})"
        if block.requirements:
            label += "\\nRequirements:\\n"
            for req_id in block.requirements:
                if req_id in self.requirements:
                    req = self.requirements[req_id]
                    # Truncate description if too long
                    desc = req.description[:40] + "..." if len(req.description) > 40 else req.description
                    label += f"{req_id}: {desc}\\n"
        return label

    def _get_domain_color(self, block: Block) -> str:
        """Get color for block based on its domain."""
        if "UI" in block.block_id:
            return "lightgreen"
        elif "MOTOR" in block.block_id:
            return "lightpink"
        elif "DOOR" in block.block_id:
            return "lightyellow"
        elif "OTA" in block.block_id or "ALARM" in block.block_id:
            return "lightgray"
        return "white"

    def _add_requirement_connections(self, dot: graphviz.Digraph, system_architecture: Block) -> None:
        """Add edges between blocks that share requirements."""
        # Create a mapping of requirements to blocks
        req_to_blocks = {}
        for block in system_architecture.subblocks:
            for req_id in block.requirements:
                if req_id not in req_to_blocks:
                    req_to_blocks[req_id] = []
                req_to_blocks[req_id].append(block.block_id)

        # Add edges between blocks that share requirements
        for req_id, block_ids in req_to_blocks.items():
            if len(block_ids) > 1:
                for i in range(len(block_ids) - 1):
                    dot.edge(block_ids[i], block_ids[i + 1], 
                           label=req_id,
                           style='dashed',
                           color='blue') 