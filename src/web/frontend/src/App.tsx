import React, { useState, useEffect } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { ChakraProvider, Box, VStack, HStack, Heading, useToast, Grid, GridItem } from '@chakra-ui/react';
import ArchitectureEditor from './components/ArchitectureEditor';
import RequirementsList from './components/RequirementsList';
import RequirementViewer from './components/RequirementViewer';
import RequirementGenerator from './components/RequirementGenerator';
import CodeGenerator from './components/CodeGenerator';
import theme from './theme';

function App() {
  const [requirements, setRequirements] = useState({});
  const [architecture, setArchitecture] = useState(null);
  const [selectedRequirement, setSelectedRequirement] = useState(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const toast = useToast();

  useEffect(() => {
    // Load initial data
    fetchRequirements();
    fetchArchitecture();
  }, []);

  const fetchRequirements = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/requirements');
      const data = await response.json();
      setRequirements(data.requirements);
    } catch (error) {
      toast({
        title: 'Error fetching requirements',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const fetchArchitecture = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/architecture');
      const data = await response.json();
      setArchitecture(data);
    } catch (error) {
      toast({
        title: 'Error fetching architecture',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleRequirementSelect = (requirement) => {
    setSelectedRequirement(requirement);
    setIsViewerOpen(true);
  };

  const handleRequirementUpdate = async (updatedRequirement) => {
    try {
      const response = await fetch(`http://localhost:8000/api/requirements/${updatedRequirement.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedRequirement),
      });

      if (!response.ok) {
        throw new Error('Failed to update requirement');
      }

      // Refresh requirements
      fetchRequirements();

      toast({
        title: 'Requirement updated',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error updating requirement',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    }
  };

  return (
    <Box minH="100vh" bg="gray.50" p={4}>
      <Heading as="h1" size="xl" mb={6}>PLM Web Interface</Heading>
      <Grid
        templateColumns={{ base: "1fr", lg: "350px 1fr" }}
        gap={6}
      >
        <GridItem>
          <VStack spacing={6} align="stretch">
            <Box bg="white" p={4} borderRadius="lg" shadow="sm">
              <RequirementGenerator onRequirementsGenerated={fetchRequirements} />
            </Box>
            <Box bg="white" p={4} borderRadius="lg" shadow="sm" overflowY="auto" maxH="calc(100vh - 400px)">
              <RequirementsList
                requirements={requirements}
                onRequirementSelect={handleRequirementSelect}
                onRequirementUpdate={handleRequirementUpdate}
              />
            </Box>
          </VStack>
        </GridItem>
        <GridItem>
          <VStack spacing={6} align="stretch">
            <Box bg="white" p={4} borderRadius="lg" shadow="sm" h="calc(100vh - 400px)">
              <ReactFlowProvider>
                <ArchitectureEditor
                  architecture={architecture}
                  onArchitectureUpdate={setArchitecture}
                />
              </ReactFlowProvider>
            </Box>
            <Box bg="white" p={4} borderRadius="lg" shadow="sm">
              <CodeGenerator requirements={requirements} />
            </Box>
          </VStack>
        </GridItem>
      </Grid>

      {selectedRequirement && (
        <RequirementViewer
          isOpen={isViewerOpen}
          onClose={() => setIsViewerOpen(false)}
          requirement={selectedRequirement}
          onEdit={() => {
            setIsViewerOpen(false);
            // Add edit functionality here
          }}
        />
      )}
    </Box>
  );
}

export default App;
