import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import {
  Box,
  VStack,
  Text,
  Badge,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
  useColorModeValue,
} from '@chakra-ui/react';

interface ArchitectureNodeProps {
  data: {
    label: string;
    domain?: string;
    description?: string;
    requirements: string[];
    onUpdate: (id: string, data: any) => void;
  };
  id: string;
}

const ArchitectureNode: React.FC<ArchitectureNodeProps> = memo(({ data, id }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Get domain-specific color
  const getDomainColor = (domain?: string) => {
    if (!domain) return 'white';
    const domainColors: { [key: string]: string } = {
      UI: 'green.50',
      BACKEND: 'blue.50',
      DATABASE: 'pink.50',
      API: 'yellow.50',
      CORE: 'gray.50',
      UTILS: 'purple.50'
    };

    for (const [key, color] of Object.entries(domainColors)) {
      if (domain.toLowerCase().includes(key.toLowerCase())) {
        return color;
      }
    }
    return 'white';
  };

  return (
    <Box
      bg={getDomainColor(data.domain)}
      border="1px"
      borderColor={borderColor}
      borderRadius="md"
      p={3}
      minWidth="200px"
      boxShadow="md"
    >
      <Handle type="target" position={Position.Top} />
      
      <VStack spacing={2} align="stretch">
        <Text fontWeight="bold" textAlign="center">
          {data.label}
        </Text>
        
        {data.domain && (
          <Badge colorScheme="gray" alignSelf="center">
            {data.domain}
          </Badge>
        )}
        
        {data.description && (
          <Text fontSize="sm" color="gray.600" noOfLines={2}>
            {data.description}
          </Text>
        )}
        
        <Popover trigger="hover" placement="right">
          <PopoverTrigger>
            <Box>
              <Badge colorScheme="blue">
                {data.requirements?.length || 0} Requirements
              </Badge>
            </Box>
          </PopoverTrigger>
          <PopoverContent>
            <PopoverArrow />
            <PopoverBody>
              <VStack align="stretch" spacing={1}>
                {data.requirements?.map((reqId) => (
                  <Text key={reqId} fontSize="sm">
                    {reqId}
                  </Text>
                ))}
              </VStack>
            </PopoverBody>
          </PopoverContent>
        </Popover>
      </VStack>
      
      <Handle type="source" position={Position.Bottom} />
    </Box>
  );
});

export default ArchitectureNode; 