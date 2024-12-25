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
import { Box, useToast, HStack, Button } from '@chakra-ui/react';
import ArchitectureNode from './ArchitectureNode';
import { debounce } from 'lodash';

// Node dimensions and spacing constants
const NODE_WIDTH = 180;
const NODE_HEIGHT = 80;
const VERTICAL_SPACING = 120;
const MIN_NODE_SPACING = 300;
const TOP_MARGIN = 40;

const nodeTypes = {
  architectureBlock: ArchitectureNode,
};

interface Block {
  name: string;
  domain?: string;
  description?: string;
  requirements?: string[];
  subblocks?: string[];
  x?: number;
  y?: number;
}

interface Architecture {
  root_id: string;
  blocks: Record<string, Block>;
}

interface ArchitectureEditorProps {
  architecture: Architecture;
  onArchitectureUpdate: (architecture: Architecture) => void;
}

const ArchitectureEditor: React.FC<ArchitectureEditorProps> = ({
  architecture,
  onArchitectureUpdate,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const toast = useToast();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Save layout changes with debounce
  const saveLayout = useCallback(
    async (updatedArchitecture: any) => {
      try {
        // Format the architecture data to match the backend's expected structure
        const formattedArchitecture = {
          blocks: {},
          root_id: updatedArchitecture.root_id
        };

        // Update block positions while preserving other data
        Object.entries(updatedArchitecture.blocks).forEach(([blockId, blockData]: [string, any]) => {
          formattedArchitecture.blocks[blockId] = {
            ...blockData,
            x: blockData.x || 0,
            y: blockData.y || 0
          };
        });

        const response = await fetch('/api/architecture/save', {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formattedArchitecture),
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || 'Failed to save layout');
        }
      } catch (error) {
        console.error("Error saving layout:", error);
        toast({
          title: "Error Saving Layout",
          description: error instanceof Error ? error.message : "Failed to save layout",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    },
    [toast]
  );

  // Debounce the save function
  const debouncedSave = useCallback(
    debounce((arch: any) => saveLayout(arch), 1000),
    [saveLayout]
  );

  const handleNodeUpdate = useCallback(
    (nodeId: string, data: any) => {
      if (!architecture?.blocks || !nodeId) {
        console.warn('Cannot update node: architecture or nodeId is missing');
        return;
      }

      const block = architecture.blocks[nodeId];
      if (!block) {
        console.warn(`Block ${nodeId} not found in architecture`);
        return;
      }

      const updatedArchitecture = { 
        ...architecture,
        blocks: {
          ...architecture.blocks,
          [nodeId]: {
            ...block,
            ...data,
          }
        }
      };
      onArchitectureUpdate(updatedArchitecture);
      debouncedSave(updatedArchitecture);
    },
    [architecture, onArchitectureUpdate, debouncedSave]
  );

  const onNodeDragStop = useCallback(
    (event: React.MouseEvent | React.TouchEvent, node: Node) => {
      if (!architecture?.blocks) {
        console.debug('Architecture not initialized yet');
        return;
      }

      if (!node?.id || !node?.position) {
        console.debug('Invalid node data', { id: node?.id, position: node?.position });
        return;
      }

      const block = architecture.blocks[node.id];
      if (!block) {
        console.debug(`Block ${node.id} not found in architecture`);
        return;
      }

      const updatedArchitecture: Architecture = {
        ...architecture,
        blocks: {
          ...architecture.blocks,
          [node.id]: {
            ...block,
            x: Math.round(node.position.x),
            y: Math.round(node.position.y),
          }
        }
      };
      onArchitectureUpdate(updatedArchitecture);
      debouncedSave(updatedArchitecture);
    },
    [architecture, onArchitectureUpdate, debouncedSave]
  );

  // Load architecture only once on mount
  useEffect(() => {
    const loadArchitecture = async () => {
      try {
        const response = await fetch('/api/architecture', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          
          if (data.nodes && data.edges) {
            console.debug('Received nodes/edges format from backend');
            
            // Process nodes with consistent dimensions
            const processedNodes = data.nodes.map((node: any) => ({
              ...node,
              type: 'architectureBlock',
              data: {
                ...node.data,
                onUpdate: handleNodeUpdate,
              },
              style: {
                width: NODE_WIDTH,
                minHeight: node.data?.description ? NODE_HEIGHT : NODE_HEIGHT * 0.6
              }
            }));

            // Create architecture object for state management
            const blocks: Record<string, Block> = {};
            processedNodes.forEach((node: any) => {
              blocks[node.id] = {
                name: node.label,
                domain: node.data?.domain,
                description: node.data?.description,
                requirements: node.data?.requirements || [],
                x: node.position.x,
                y: node.position.y
              };
            });

            const architectureData = {
              root_id: processedNodes[0]?.id || 'BLK-SYSTEM',
              blocks
            };

            // Set initial data
            setNodes(processedNodes);
            setEdges(data.edges);
            onArchitectureUpdate(architectureData);

            // Calculate initial layout if all positions are at (0,0)
            const needsLayout = processedNodes.every(node => 
              node.position.x === 0 && node.position.y === 0
            );

            if (needsLayout) {
              // Create parent-child relationships
              const parentToChildren: Record<string, string[]> = {};
              data.edges.forEach((edge: any) => {
                if (!edge.source || !edge.target || edge.label) return;
                if (!parentToChildren[edge.source]) {
                  parentToChildren[edge.source] = [];
                }
                parentToChildren[edge.source].push(edge.target);
              });

              // Calculate levels
              const nodeLevels: Record<string, number> = {};
              const calculateLevels = (nodeId: string, level: number) => {
                nodeLevels[nodeId] = level;
                const children = parentToChildren[nodeId] || [];
                children.forEach(childId => calculateLevels(childId, level + 1));
              };
              calculateLevels(architectureData.root_id, 0);

              // Group by levels
              const levelGroups: Record<number, string[]> = {};
              Object.entries(nodeLevels).forEach(([nodeId, level]) => {
                if (!levelGroups[level]) levelGroups[level] = [];
                levelGroups[level].push(nodeId);
              });

              // Calculate positions
              const updatedNodes = processedNodes.map(node => {
                const level = nodeLevels[node.id] || 0;
                const nodesInLevel = levelGroups[level] || [];
                const indexInLevel = nodesInLevel.indexOf(node.id);
                const totalInLevel = nodesInLevel.length;

                const x = (indexInLevel - (totalInLevel - 1) / 2) * MIN_NODE_SPACING;
                const y = level * VERTICAL_SPACING + TOP_MARGIN;

                return {
                  ...node,
                  position: { x, y }
                };
              });

              setNodes(updatedNodes);

              // Update architecture with new positions
              const updatedBlocks = { ...blocks };
              updatedNodes.forEach(node => {
                if (updatedBlocks[node.id]) {
                  updatedBlocks[node.id].x = node.position.x;
                  updatedBlocks[node.id].y = node.position.y;
                }
              });

              onArchitectureUpdate({
                ...architectureData,
                blocks: updatedBlocks
              });
            }
          } else {
            onArchitectureUpdate(data);
          }
        } else {
          toast({
            title: "Error loading architecture",
            description: `Server returned ${response.status}: ${response.statusText}`,
            status: "error",
            duration: 5000,
            isClosable: true,
          });
        }
      } catch (error) {
        console.error("Error loading architecture:", error);
        toast({
          title: "Connection Error",
          description: "Could not connect to the backend server. Please ensure the server is running.",
          status: "error",
          duration: null,
          isClosable: true,
        });
      }
    };

    if (!architecture || !architecture.blocks) {
      loadArchitecture();
    }
  }, []); // Only run once on mount

  // Update layout when architecture changes (e.g., after generation)
  useEffect(() => {
    if (!architecture?.blocks || !architecture?.root_id || !edges.length) {
      return;
    }

    // Create a map of parent to children relationships
    const parentToChildren: Record<string, string[]> = {};
    edges.forEach(edge => {
      if (!edge.source || !edge.target) return;
      if (!parentToChildren[edge.source]) {
        parentToChildren[edge.source] = [];
      }
      // Only consider structural edges (without requirement labels)
      if (!edge.label) {
        parentToChildren[edge.source].push(edge.target);
      }
    });

    // Calculate levels for each node
    const nodeLevels: Record<string, number> = {};
    const calculateLevels = (nodeId: string, level: number) => {
      nodeLevels[nodeId] = level;
      const children = parentToChildren[nodeId] || [];
      children.forEach(childId => calculateLevels(childId, level + 1));
    };

    // Start from the root node
    calculateLevels(architecture.root_id, 0);

    // Group nodes by level
    const levelGroups: Record<number, string[]> = {};
    Object.entries(nodeLevels).forEach(([nodeId, level]) => {
      if (!levelGroups[level]) levelGroups[level] = [];
      levelGroups[level].push(nodeId);
    });

    // Calculate positions with adjusted spacing
    const VERTICAL_SPACING = 120;
    const MIN_NODE_SPACING = 300;
    const TOP_MARGIN = 40;
    const NODE_WIDTH = 180;
    const NODE_HEIGHT = 80;

    // First pass: calculate total width needed for each level
    const levelWidths: Record<number, number> = {};
    Object.entries(levelGroups).forEach(([level, nodes]) => {
      const totalWidth = nodes.length * MIN_NODE_SPACING;
      levelWidths[parseInt(level)] = totalWidth;
    });

    // Find the maximum width needed
    const maxWidth = Math.max(...Object.values(levelWidths));

    // Second pass: position nodes
    const updatedNodes = nodes.map(node => {
      // If node has saved position, use it
      if (architecture.blocks[node.id]?.x !== undefined && 
          architecture.blocks[node.id]?.y !== undefined) {
        return {
          ...node,
          position: {
            x: architecture.blocks[node.id].x || 0,
            y: architecture.blocks[node.id].y || 0
          }
        };
      }

      // Otherwise calculate new position
      const level = nodeLevels[node.id] || 0;
      const nodesInLevel = levelGroups[level] || [];
      const indexInLevel = nodesInLevel.indexOf(node.id);
      const totalInLevel = nodesInLevel.length;

      const levelWidth = levelWidths[level];
      const startX = -(maxWidth / 2);
      const spacing = Math.max(MIN_NODE_SPACING, maxWidth / totalInLevel);
      const x = startX + (indexInLevel * spacing) + (spacing / 2);
      const y = (level * VERTICAL_SPACING) + TOP_MARGIN;

      return {
        ...node,
        position: { x, y }
      };
    });

    setNodes(updatedNodes);
  }, [architecture?.root_id]); // Only run when root_id changes (i.e., new architecture generated)

  return (
    <Box 
      height="45vh"
      width="100%" 
      border="1px" 
      borderColor="gray.200" 
      borderRadius="md"
      display="flex"
      flexDirection="column"
      overflow="hidden"
    >
      <HStack p={2} spacing={4} borderBottom="1px" borderColor="gray.200">
        <Button
          colorScheme="blue"
          size="sm"
          onClick={async () => {
            try {
              const response = await fetch('/api/architecture/generate');
              if (!response.ok) {
                const error = await response.json();
                toast({
                  title: "Failed to generate architecture",
                  description: error.error || "Please run code analysis first",
                  status: "error",
                  duration: 5000,
                  isClosable: true,
                });
                return;
              }
              const newArchitecture = await response.json();
              onArchitectureUpdate(newArchitecture);
              toast({
                title: "Architecture generated",
                description: "System architecture has been generated from code analysis",
                status: "success",
                duration: 3000,
                isClosable: true,
              });
            } catch (error) {
              console.error("Error generating architecture:", error);
              toast({
                title: "Error",
                description: "Failed to generate architecture",
                status: "error",
                duration: 5000,
                isClosable: true,
              });
            }
          }}
        >
          Generate from Code
        </Button>
      </HStack>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ 
          padding: 0.2,
          includeHiddenNodes: true,
          minZoom: 0.2,
          maxZoom: 0.8
        }}
        minZoom={0.1}
        maxZoom={1.5}
        defaultViewport={{ x: 0, y: 0, zoom: 0.4 }}
        style={{ flex: 1 }}
      >
        <Background />
        <Controls />
      </ReactFlow>
    </Box>
  );
};

export default ArchitectureEditor; 