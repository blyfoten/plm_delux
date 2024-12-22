import React, { useState } from 'react';
import {
  Box,
  Button,
  Code,
  Heading,
  Select,
  VStack,
  useToast,
  Text,
} from '@chakra-ui/react';

interface Requirement {
  id: string;
  description: string;
}

interface CodeGeneratorProps {
  requirements: Record<string, Requirement>;
}

const CodeGenerator: React.FC<CodeGeneratorProps> = ({ requirements }) => {
  const [selectedRequirement, setSelectedRequirement] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const toast = useToast();

  const handleGenerate = async () => {
    if (!selectedRequirement) {
      toast({
        title: 'Error',
        description: 'Please select a requirement',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/api/code/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ requirement_id: selectedRequirement }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate code');
      }

      const data = await response.json();
      setGeneratedCode(data.code);
      toast({
        title: 'Success',
        description: 'Code generated successfully',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const requirementOptions = React.useMemo(() => {
    if (!requirements) return [];
    return Object.entries(requirements).map(([id, req]) => ({
      value: id,
      label: `${id}: ${req.description}`
    }));
  }, [requirements]);

  if (!requirements || Object.keys(requirements).length === 0) {
    return (
      <Box p={4} borderWidth="1px" borderRadius="lg">
        <Text color="gray.500" textAlign="center">No requirements available for code generation</Text>
      </Box>
    );
  }

  return (
    <Box p={4} borderWidth="1px" borderRadius="lg">
      <VStack spacing={4} align="stretch">
        <Heading size="md">Code Generator</Heading>
        
        <Select
          placeholder="Select a requirement"
          value={selectedRequirement}
          onChange={(e) => setSelectedRequirement(e.target.value)}
        >
          {requirementOptions.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>

        <Button
          colorScheme="blue"
          onClick={handleGenerate}
          isLoading={isGenerating}
          loadingText="Generating..."
        >
          Generate Code
        </Button>

        {generatedCode && (
          <Box>
            <Text fontWeight="bold" mb={2}>
              Generated Code:
            </Text>
            <Box
              p={4}
              bg="gray.50"
              borderRadius="md"
              maxHeight="400px"
              overflowY="auto"
            >
              <Code display="block" whiteSpace="pre">
                {generatedCode}
              </Code>
            </Box>
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default CodeGenerator; 