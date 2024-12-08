import React, { useCallback, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Connection,
  addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Box, useToast } from '@chakra-ui/react';
import ArchitectureNode from './ArchitectureNode';

const nodeTypes = {
  architectureBlock: ArchitectureNode,
};

interface ArchitectureEditorProps {
  architecture: any;
  onArchitectureUpdate: (architecture: any) => void;
}

const ArchitectureEditor: React.FC<ArchitectureEditorProps> = ({
  architecture,
  onArchitectureUpdate,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const toast = useToast();

  // Convert architecture to nodes and edges
  useEffect(() => {
    if (!architecture) return;

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    const processedBlocks = new Set();

    const processBlock = (block: any, parentId?: string, level = 0) => {
      if (processedBlocks.has(block.block_id)) return;
      processedBlocks.add(block.block_id);

      // Create node
      newNodes.push({
        id: block.block_id,
        type: 'architectureBlock',
        position: { x: block.x || level * 250, y: block.y || level * 150 },
        data: {
          label: block.name,
          requirements: block.requirements,
          onUpdate: handleNodeUpdate,
        },
      });

      // Create edge from parent if exists
      if (parentId) {
        newEdges.push({
          id: `${parentId}-${block.block_id}`,
          source: parentId,
          target: block.block_id,
          type: 'smoothstep',
        });
      }

      // Process subblocks
      block.subblocks?.forEach((subblockId: string) => {
        const subblock = architecture.blocks?.[subblockId];
        if (subblock) {
          processBlock(subblock, block.block_id, level + 1);
        }
      });
    };

    processBlock(architecture);
    setNodes(newNodes);
    setEdges(newEdges);
  }, [architecture, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleNodeUpdate = useCallback(
    (nodeId: string, data: any) => {
      const updatedArchitecture = { ...architecture };
      updatedArchitecture.blocks[nodeId] = {
        ...updatedArchitecture.blocks[nodeId],
        ...data,
      };
      onArchitectureUpdate(updatedArchitecture);
    },
    [architecture, onArchitectureUpdate]
  );

  const onNodeDragStop = useCallback(
    (event: any, node: Node) => {
      const updatedArchitecture = { ...architecture };
      updatedArchitecture.blocks[node.id] = {
        ...updatedArchitecture.blocks[node.id],
        x: node.position.x,
        y: node.position.y,
      };
      onArchitectureUpdate(updatedArchitecture);
    },
    [architecture, onArchitectureUpdate]
  );

  useEffect(() => {
    // Fetch the latest architecture diagram
    const fetchArchitecture = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/architecture');
        const data = await response.json();
        setArchitecture(data);
      } catch (error) {
        console.error('Error fetching architecture:', error);
      }
    };

    fetchArchitecture();
  }, []); // Empty dependency array means this runs once on component mount

  return (
    <Box height="100%" border="1px" borderColor="gray.200" borderRadius="md">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </Box>
  );
};

export default ArchitectureEditor; 