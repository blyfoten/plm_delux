import React, { useState, useEffect } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { ChakraProvider, Box, VStack, HStack, Heading, useToast, Grid, GridItem, IconButton, useDisclosure } from '@chakra-ui/react';
import { SettingsIcon } from '@chakra-ui/icons';
import ArchitectureEditor from './components/ArchitectureEditor';
import RequirementsList from './components/RequirementsList';
import RequirementViewer from './components/RequirementViewer';
import RequirementGenerator from './components/RequirementGenerator';
import CodeGenerator from './components/CodeGenerator';
import { SettingsDialog } from './components/SettingsDialog';
import theme from './theme';

function App() {
  const [requirements, setRequirements] = useState({});
  const [architecture, setArchitecture] = useState(null);
  const [selectedRequirement, setSelectedRequirement] = useState(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const { isOpen: isSettingsOpen, onOpen: openSettings, onClose: closeSettings } = useDisclosure();
  const [isSettingsConfigured, setIsSettingsConfigured] = useState(false);

  useEffect(() => {
    // Load initial data
    fetchRequirements();
    fetchArchitecture();
    // Check if settings exist when app loads
    checkSettings();
  }, []);

  const checkSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/settings');
      const data = await response.json();
      
      // Consider settings as configured if they've been customized from defaults
      // or if the settings file exists (any response means file exists)
      setIsSettingsConfigured(true);
      
      // If settings don't exist, open settings dialog
      if (!response.ok || response.status === 404) {
        openSettings();
      }
    } catch (error) {
      console.error('Error checking settings:', error);
      setIsSettingsConfigured(false);
      openSettings();
    }
  };

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

  const handleSettingsSave = () => {
    setIsSettingsConfigured(true);
    closeSettings();
  };

  return (
    <Box minH="100vh" bg="gray.50" p={4}>
      <HStack justify="space-between" mb={6}>
        <Heading as="h1" size="xl">PLM Web Interface</Heading>
        <IconButton
          aria-label="Settings"
          icon={<SettingsIcon />}
          onClick={openSettings}
          variant="ghost"
        />
      </HStack>
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

      <SettingsDialog
        isOpen={isSettingsOpen}
        onClose={isSettingsConfigured ? closeSettings : undefined}
        onSave={handleSettingsSave}
        forceConfiguration={!isSettingsConfigured}
      />
    </Box>
  );
}

export default App;
