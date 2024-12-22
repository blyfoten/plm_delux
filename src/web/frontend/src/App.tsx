import React, { useState, useEffect } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { ChakraProvider, Box, VStack, HStack, Heading, useToast, Grid, GridItem, IconButton, useDisclosure, Tabs, TabList, TabPanels, Tab, TabPanel } from '@chakra-ui/react';
import { SettingsIcon } from '@chakra-ui/icons';
import ArchitectureEditor from './components/ArchitectureEditor';
import RequirementsList from './components/RequirementsList';
import RequirementViewer from './components/RequirementViewer';
import RequirementGenerator from './components/RequirementGenerator';
import CodeGenerator from './components/CodeGenerator';
import { SettingsDialog } from './components/SettingsDialog';
import theme from './theme';
import CodeAnalyzer from './components/CodeAnalyzer';

// Add type interfaces
interface Requirement {
  id: string;
  domain: string;
  description: string;
  linked_blocks: string[];
  additional_notes: string[];
  content: string;
  code_references: Array<{
    file: string;
    line: number;
    function: string;
    type: string;
    url: string;
  }>;
}

interface Architecture {
  root_id: string;
  blocks: Record<string, {
    block_id: string;
    name: string;
    requirements: string[];
    subblocks: string[];
    x: number;
    y: number;
  }>;
}

// Add after imports
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
console.log('Using backend URL:', BACKEND_URL);

function App() {
  const [requirements, setRequirements] = useState<Record<string, Requirement>>({});
  const [architecture, setArchitecture] = useState<Architecture | null>(null);
  const [selectedRequirement, setSelectedRequirement] = useState<Requirement | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const { isOpen: isSettingsOpen, onOpen: openSettings, onClose: closeSettings } = useDisclosure();
  const [isSettingsConfigured, setIsSettingsConfigured] = useState(false);
  const toast = useToast();

  useEffect(() => {
    // Load initial data
    fetchRequirements();
    fetchArchitecture();
    // Check if settings exist when app loads
    checkSettings();
  }, []);

  const checkSettings = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/settings`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load settings');
      }
      
      const data = await response.json();
      
      // Consider settings as configured if they've been customized from defaults
      setIsSettingsConfigured(true);
      
      // If settings are empty or have default values, open settings dialog
      if (!data || Object.keys(data).length === 0) {
        openSettings();
      }
    } catch (error) {
      console.error('Error checking settings:', error);
      toast({
        title: 'Error loading settings',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      setIsSettingsConfigured(false);
      openSettings();
    }
  };

  const fetchRequirements = async () => {
    console.log('Fetching requirements from:', `${BACKEND_URL}/api/requirements`);
    try {
      const response = await fetch(`${BACKEND_URL}/api/requirements`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
          'Origin': window.location.origin
        },
        mode: 'cors',
        credentials: 'include'
      });
      
      console.log('Requirements API response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Requirements API error:', errorData);
        throw new Error(errorData.error || 'Failed to fetch requirements');
      }
      
      const requirementsArray = await response.json();
      console.log('Requirements API response data:', requirementsArray);
      
      // Convert array to Record<string, Requirement>
      const requirementsMap = requirementsArray.reduce((acc, req) => {
        acc[req.id] = req;
        return acc;
      }, {});
      
      console.log('Converted requirements map:', requirementsMap);
      setRequirements(requirementsMap);
    } catch (error) {
      console.error('Error in fetchRequirements:', error);
      toast({
        title: 'Error fetching requirements',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleAnalysisComplete = async () => {
    try {
      // First fetch the analysis results
      const analysisResponse = await fetch(`${BACKEND_URL}/api/analyze/results`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!analysisResponse.ok) {
        throw new Error('Failed to fetch analysis results');
      }
      
      const analysisData = await analysisResponse.json();
      
      // For each analyzed file, create a requirement
      for (const [filePath, fileAnalysis] of Object.entries(analysisData)) {
        const domain = fileAnalysis.domain || 'Uncategorized';
        const reqId = `RQ-${filePath.replace(/[^a-zA-Z0-9]/g, '_')}`;
        
        // Create a new requirement from the analysis
        const newRequirement = {
          id: reqId,
          domain: domain,
          description: fileAnalysis.purpose || 'No description available',
          linked_blocks: [],
          additional_notes: [
            ...(fileAnalysis.key_functionality || []),
            ...(fileAnalysis.implementation_details || [])
          ],
          implementation_files: [filePath],
          code_references: fileAnalysis.functions.map(fn => ({
            file: filePath,
            line: fn.line_number,
            function: fn.name,
            type: 'function',
            url: `#${filePath}:${fn.line_number}`
          }))
        };
        
        // Create the requirement via the requirements API
        await fetch(`${BACKEND_URL}/api/requirements`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(newRequirement)
        });
      }
      
      // Refresh the requirements list
      fetchRequirements();
      
      toast({
        title: 'Analysis Complete',
        description: 'Requirements have been generated from analysis results',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error processing analysis results',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const fetchArchitecture = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/architecture`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch architecture');
      }
      
      const data = await response.json();
      setArchitecture(data);
    } catch (error) {
      toast({
        title: 'Error fetching architecture',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleRequirementSelect = (requirement: Requirement) => {
    setSelectedRequirement(requirement);
    setIsViewerOpen(true);
  };

  const handleRequirementUpdate = async (updatedRequirement: Requirement) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/requirements/${updatedRequirement.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
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
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error updating requirement',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
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
              <Tabs>
                <TabList>
                  <Tab>Architecture</Tab>
                  <Tab>Code Analysis</Tab>
                </TabList>
                <TabPanels>
                  <TabPanel p={0}>
                    <ReactFlowProvider>
                      <ArchitectureEditor
                        architecture={architecture}
                        onArchitectureUpdate={setArchitecture}
                      />
                    </ReactFlowProvider>
                  </TabPanel>
                  <TabPanel p={0}>
                    <CodeAnalyzer onAnalysisComplete={handleAnalysisComplete} />
                  </TabPanel>
                </TabPanels>
              </Tabs>
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
