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
    if (!architecture || !architecture.blocks) return;

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    const processedBlocks = new Set();

    // Calculate initial positions for blocks
    const calculatePosition = (blockId: string, level: number, index: number, totalInLevel: number) => {
      const LEVEL_HEIGHT = 150;
      const LEVEL_WIDTH = 1200;
      const BLOCK_SPACING = LEVEL_WIDTH / (totalInLevel + 1);
      
      return {
        x: BLOCK_SPACING * (index + 1) - LEVEL_WIDTH / 2,
        y: level * LEVEL_HEIGHT
      };
    };

    // First pass: count blocks per level
    const blocksPerLevel: { [level: number]: number } = {};
    const blockLevels: { [blockId: string]: number } = {};

    const countBlocksInLevel = (blockId: string, level: number) => {
      blocksPerLevel[level] = (blocksPerLevel[level] || 0) + 1;
      blockLevels[blockId] = level;

      const block = architecture.blocks[blockId];
      if (block?.subblocks) {
        block.subblocks.forEach(subId => {
          countBlocksInLevel(subId, level + 1);
        });
      }
    };

    countBlocksInLevel(architecture.root_id, 0);

    // Second pass: create nodes and edges
    const levelCounters: { [level: number]: number } = {};

    const processBlock = (blockId: string) => {
      if (processedBlocks.has(blockId)) return;
      processedBlocks.add(blockId);

      const block = architecture.blocks[blockId];
      if (!block) return;

      const level = blockLevels[blockId];
      levelCounters[level] = (levelCounters[level] || 0);

      // Calculate position
      const position = calculatePosition(
        blockId,
        level,
        levelCounters[level],
        blocksPerLevel[level]
      );
      levelCounters[level]++;

      // Create node
      newNodes.push({
        id: blockId,
        type: 'architectureBlock',
        position: { 
          x: block.x || position.x,
          y: block.y || position.y
        },
        data: {
          label: block.name,
          requirements: block.requirements || [],
          onUpdate: handleNodeUpdate,
        },
      });

      // Process subblocks and create edges
      if (block.subblocks) {
        block.subblocks.forEach(subId => {
          // Create edge
          newEdges.push({
            id: `${blockId}-${subId}`,
            source: blockId,
            target: subId,
            type: 'smoothstep',
          });

          // Process subblock
          processBlock(subId);
        });
      }

      // Add requirement connections
      if (block.requirements) {
        block.requirements.forEach(reqId => {
          // Find other blocks with the same requirement
          Object.entries(architecture.blocks).forEach(([otherId, otherBlock]: [string, any]) => {
            if (otherId !== blockId && otherBlock.requirements?.includes(reqId)) {
              newEdges.push({
                id: `${blockId}-${otherId}-${reqId}`,
                source: blockId,
                target: otherId,
                label: reqId,
                type: 'smoothstep',
                style: { stroke: '#2B6CB0', strokeDasharray: '5,5' },
                animated: true,
              });
            }
          });
        });
      }
    };

    processBlock(architecture.root_id);
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