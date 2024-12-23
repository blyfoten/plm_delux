import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Progress,
  Text,
  VStack,
  HStack,
  Heading,
  Badge,
  useToast,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  List,
  ListItem,
  Divider,
  Spinner,
  Tag,
  TagLabel,
  Grid,
  GridItem,
  ButtonGroup,
  Checkbox,
  Center,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
} from '@chakra-ui/react';

const BACKEND_URL = '';

interface FileAnalysis {
  file_path: string;
  language: string;
  purpose: string;
  key_functionality: string[];
  dependencies: string[];
  interfaces: string[];
  implementation_details: string[];
  potential_issues: string[];
  domain: string | null;
}

interface AnalysisProgress {
  total_files: number;
  analyzed_files: number;
  current_file: string | null;
  status: 'idle' | 'running' | 'completed' | 'error';
  error_message: string | null;
}

interface CodeAnalyzerProps {
  onAnalysisComplete?: () => void;
}

// Add console logging helper
const log = {
  info: (message: string, data?: any) => {
    console.log(`[CodeAnalyzer] ${message}`, data || '');
  },
  error: (message: string, error: any) => {
    console.error(`[CodeAnalyzer] ${message}:`, error);
  },
  debug: (message: string, data?: any) => {
    console.debug(`[CodeAnalyzer] ${message}`, data || '');
  }
};

// Fix NodeJS type error
type TimeoutHandle = ReturnType<typeof setTimeout>;

// Add helper to check if response is HTML instead of JSON
const isHtmlResponse = (text: string) => {
  return text.trim().toLowerCase().startsWith('<!doctype') || text.trim().toLowerCase().startsWith('<html');
};

// Add helper to get meaningful error message
const getErrorMessage = async (response: Response) => {
  const text = await response.text();
  if (isHtmlResponse(text)) {
    return `Server returned HTML instead of JSON. Status: ${response.status}. This usually means the backend server is not running or returned an error page.`;
  }
  return text;
};

// Add new interfaces
interface DomainRecommendation {
  domain_id: string;
  name: string;
  description: string;
  subdomain_ids: string[];
  confidence: number;
  reasoning: string;
}

interface DomainRecommendations {
  recommendations: DomainRecommendation[];
  changes_detected: boolean;
}

const CodeAnalyzer: React.FC<CodeAnalyzerProps> = ({ onAnalysisComplete }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoadingCache, setIsLoadingCache] = useState(true);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [progress, setProgress] = useState<AnalysisProgress>({
    total_files: 0,
    analyzed_files: 0,
    current_file: null,
    status: 'idle',
    error_message: null,
  });
  const [results, setResults] = useState<Record<string, FileAnalysis>>({});
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const toast = useToast();
  const { isOpen: isRecommendationsOpen, onOpen: onRecommendationsOpen, onClose: onRecommendationsClose } = useDisclosure();
  const [domainRecommendations, setDomainRecommendations] = useState<DomainRecommendations | null>(null);
  const [isGeneratingRequirements, setIsGeneratingRequirements] = useState(false);
  const [isCheckingDomains, setIsCheckingDomains] = useState(false);
  const [availableDomains, setAvailableDomains] = useState<string[]>([]);

  // Load cached results on mount
  useEffect(() => {
    const loadCachedResults = async () => {
      log.info('Loading cached analysis results...');
      try {
        setIsLoadingCache(true);
        const response = await fetch(`${BACKEND_URL}/api/analyze/results`, {
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });
        log.debug('Cache response status:', response.status);
        
        if (response.ok) {
          const text = await response.text();
          if (isHtmlResponse(text)) {
            throw new Error('Server returned HTML instead of JSON. Backend may not be running.');
          }
          const data = JSON.parse(text);
          log.info('Loaded cached results:', { fileCount: Object.keys(data).length });
          setResults(data);
          setProgress({
            total_files: Object.keys(data).length,
            analyzed_files: Object.keys(data).length,
            current_file: null,
            status: 'completed',
            error_message: null,
          });
        } else {
          const errorMsg = await getErrorMessage(response);
          log.error('Failed to load cache', errorMsg);
          throw new Error(errorMsg);
        }
      } catch (error) {
        log.error('Error loading cached results:', error);
        const message = error instanceof Error ? error.message : 'Failed to load cached analysis results';
        toast({
          title: 'Backend Connection Error',
          description: message,
          status: 'error',
          duration: 10000,
          isClosable: true,
        });
      } finally {
        setIsLoadingCache(false);
      }
    };

    loadCachedResults();
  }, [toast]);

  // Poll for progress updates when analysis is running
  useEffect(() => {
    let pollInterval: NodeJS.Timeout;

    const pollProgress = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/analyze/progress`, {
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to fetch analysis progress');
        }

        const text = await response.text();
        if (text.trim().toLowerCase().startsWith('<!doctype') || text.trim().toLowerCase().startsWith('<html')) {
          throw new Error('Server returned HTML instead of JSON. Backend may not be running.');
        }

        const data = JSON.parse(text);
        setProgress(data);

        if (data.status === 'completed' || data.status === 'error') {
          setIsAnalyzing(false);
          clearInterval(pollInterval);

          if (data.status === 'completed') {
            await fetchResults();
            if (onAnalysisComplete) {
              onAnalysisComplete();
            }
            toast({
              title: 'Analysis Complete',
              description: 'Code analysis has finished successfully',
              status: 'success',
              duration: 3000,
              isClosable: true
            });
          } else if (data.status === 'error') {
            toast({
              title: 'Analysis Error',
              description: data.error_message || 'An error occurred during analysis',
              status: 'error',
              duration: 5000,
              isClosable: true
            });
          }
        }
      } catch (error) {
        console.error('Error polling progress:', error);
        setIsAnalyzing(false);
        clearInterval(pollInterval);
        toast({
          title: 'Connection Error',
          description: error instanceof Error ? error.message : 'Failed to connect to backend server',
          status: 'error',
          duration: 5000,
          isClosable: true
        });
      }
    };

    if (isAnalyzing) {
      pollInterval = setInterval(pollProgress, 1000);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [isAnalyzing, onAnalysisComplete, toast]);

  // Function to start analysis of all files
  const startAnalysis = async () => {
    log.info('Starting analysis of all files');
    try {
      setIsAnalyzing(true);
      const response = await fetch(`${BACKEND_URL}/api/analyze/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ files: null }),
      });
      log.debug('Start analysis response status:', response.status);

      if (!response.ok) {
        const errorMsg = await getErrorMessage(response);
        log.error('Failed to start analysis', errorMsg);
        throw new Error(errorMsg);
      }

      const text = await response.text();
      if (isHtmlResponse(text)) {
        throw new Error('Server returned HTML instead of JSON. Backend may not be running.');
      }
      
      const responseData = JSON.parse(text);
      log.info('Analysis started successfully:', responseData);

      toast({
        title: 'Analysis Started',
        description: 'Starting analysis of all files...',
        status: 'info',
        duration: 3000,
      });
    } catch (error) {
      log.error('Error starting analysis:', error);
      setIsAnalyzing(false);
      toast({
        title: 'Backend Connection Error',
        description: error instanceof Error ? error.message : 'Failed to connect to backend server',
        status: 'error',
        duration: 10000,
        isClosable: true,
      });
    }
  };

  // Function to analyze selected files
  const analyzeSelectedFiles = async () => {
    if (selectedFiles.length === 0) {
      log.info('No files selected for analysis');
      toast({
        title: 'No Files Selected',
        description: 'Please select at least one file to analyze',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    log.info('Starting analysis of selected files:', selectedFiles);
    try {
      setIsAnalyzing(true);
      const response = await fetch(`${BACKEND_URL}/api/analyze/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ files: selectedFiles }),
      });
      log.debug('Start analysis response status:', response.status);

      if (!response.ok) {
        const errorMsg = await getErrorMessage(response);
        log.error('Failed to start analysis', errorMsg);
        throw new Error(errorMsg);
      }

      const text = await response.text();
      if (isHtmlResponse(text)) {
        throw new Error('Server returned HTML instead of JSON. Backend may not be running.');
      }
      
      const responseData = JSON.parse(text);
      log.info('Analysis started successfully:', responseData);

      toast({
        title: 'Analysis Started',
        description: `Analyzing ${selectedFiles.length} selected files...`,
        status: 'info',
        duration: 3000,
      });
    } catch (error) {
      log.error('Error starting analysis:', error);
      setIsAnalyzing(false);
      toast({
        title: 'Backend Connection Error',
        description: error instanceof Error ? error.message : 'Failed to connect to backend server',
        status: 'error',
        duration: 10000,
        isClosable: true,
      });
    }
  };

  // Function to toggle file selection
  const toggleFileSelection = (filePath: string) => {
    setSelectedFiles(prev => 
      prev.includes(filePath) 
        ? prev.filter(f => f !== filePath)
        : [...prev, filePath]
    );
  };

  // Group results by domain
  const resultsByDomain = Object.entries(results).reduce((acc, [filePath, analysis]) => {
    const domain = analysis.domain || 'unknown';
    if (!acc[domain]) {
      acc[domain] = [];
    }
    acc[domain].push({ filePath, ...analysis });
    return acc;
  }, {} as Record<string, (FileAnalysis & { filePath: string })[]>);

  const fetchResults = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analyze/results`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch analysis results');
      }

      const text = await response.text();
      if (text.trim().toLowerCase().startsWith('<!doctype') || text.trim().toLowerCase().startsWith('<html')) {
        throw new Error('Server returned HTML instead of JSON. Backend may not be running.');
      }

      const data = JSON.parse(text);
      
      if (data.status === 'error') {
        throw new Error(data.error || 'Unknown error occurred');
      }

      if (data.status === 'no_results') {
        setResults({});
        return;
      }

      setResults(data.results || {});
    } catch (error) {
      console.error('[CodeAnalyzer] Error loading cached results:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to fetch analysis results',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  };

  // Function to check domain recommendations
  const checkDomainRecommendations = async () => {
    try {
      setIsCheckingDomains(true);
      const response = await fetch(`${BACKEND_URL}/api/analyze/recommend-domains`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const recommendations = await response.json();
      setDomainRecommendations(recommendations);

      if (recommendations.changes_detected) {
        onRecommendationsOpen();
      } else {
        toast({
          title: 'Domain Check Complete',
          description: 'Current domain structure is optimal for the codebase.',
          status: 'success',
          duration: 5000,
        });
      }
    } catch (error) {
      log.error('Error checking domain recommendations:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to check domain recommendations',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsCheckingDomains(false);
    }
  };

  // Function to apply domain recommendations
  const applyDomainRecommendations = async () => {
    try {
      if (!domainRecommendations) return;

      // First, fetch current settings
      const settingsResponse = await fetch(`${BACKEND_URL}/api/settings`);
      if (!settingsResponse.ok) {
        throw new Error(await getErrorMessage(settingsResponse));
      }
      const currentSettings = await settingsResponse.json();

      // Update settings with new domain structure while preserving other settings
      const response = await fetch(`${BACKEND_URL}/api/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...currentSettings,  // Preserve all existing settings
          domains: domainRecommendations.recommendations.reduce((acc, rec) => ({
            ...acc,
            [rec.domain_id]: {
              name: rec.name,
              description: rec.description,
              subdomain_ids: rec.subdomain_ids,
            }
          }), {})
        })
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      toast({
        title: 'Domains Updated',
        description: 'Domain structure has been updated successfully.',
        status: 'success',
        duration: 5000,
      });

      // Refresh results to show new domain assignments
      await fetchResults();
      onRecommendationsClose();
    } catch (error) {
      log.error('Error applying domain recommendations:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to apply domain recommendations',
        status: 'error',
        duration: 5000,
      });
    }
  };

  // Function to generate requirements
  const generateRequirements = async () => {
    try {
      setIsGeneratingRequirements(true);
      const response = await fetch(`${BACKEND_URL}/api/analyze/generate-requirements`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          files: selectedFiles.length > 0 ? selectedFiles : null
        })
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const result = await response.json();
      toast({
        title: 'Requirements Generated',
        description: `Generated ${result.requirements.length} requirements in ${result.generated_files.length} files.`,
        status: 'success',
        duration: 5000,
      });

      // Show a more detailed toast with file paths
      if (result.generated_files.length > 0) {
        toast({
          title: 'Generated Files',
          description: (
            <VStack align="stretch" spacing={1}>
              {result.generated_files.map((file: string, index: number) => (
                <Text key={index} fontSize="sm">{file}</Text>
              ))}
            </VStack>
          ),
          status: 'info',
          duration: 10000,
          isClosable: true,
        });
      }

      // Refresh requirements listing
      const reqResponse = await fetch(`${BACKEND_URL}/api/requirements`);
      if (reqResponse.ok) {
        const reqData = await reqResponse.json();
        // Assuming you have a requirements state and setter from props or context
        if (onAnalysisComplete) {
          onAnalysisComplete();
        }
      }
    } catch (error) {
      log.error('Error generating requirements:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to generate requirements',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsGeneratingRequirements(false);
    }
  };

  // Add useEffect to fetch available domains from settings
  useEffect(() => {
    const fetchDomains = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/settings`);
        if (!response.ok) {
          throw new Error(await getErrorMessage(response));
        }
        const settings = await response.json();
        setAvailableDomains(Object.keys(settings.domains));
      } catch (error) {
        log.error('Error fetching domains:', error);
      }
    };
    fetchDomains();
  }, []);

  return (
    <VStack spacing={6} align="stretch" height="100%">
      <HStack justify="space-between">
        <Heading size="md">Code Analysis</Heading>
        <ButtonGroup>
          <Button
            colorScheme="purple"
            onClick={generateRequirements}
            isLoading={isGeneratingRequirements}
            loadingText="Generating..."
          >
            Generate Requirements
          </Button>
          <Button
            colorScheme="teal"
            onClick={checkDomainRecommendations}
            isLoading={isCheckingDomains}
            loadingText="Checking..."
          >
            Check Domains
          </Button>
          <Button
            colorScheme="blue"
            onClick={analyzeSelectedFiles}
            isLoading={isAnalyzing}
            loadingText="Analyzing..."
            isDisabled={selectedFiles.length === 0}
          >
            Analyze Selected ({selectedFiles.length})
          </Button>
          <Button
            colorScheme="blue"
            onClick={startAnalysis}
            isLoading={isAnalyzing}
            loadingText="Analyzing All..."
          >
            Analyze All Files
          </Button>
        </ButtonGroup>
      </HStack>

      {/* Domain Recommendations Modal */}
      <Modal isOpen={isRecommendationsOpen} onClose={onRecommendationsClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Domain Structure Recommendations</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack align="stretch" spacing={4}>
              {domainRecommendations?.recommendations.map((rec) => (
                <Box key={rec.domain_id} p={4} borderWidth={1} borderRadius="md">
                  <HStack justify="space-between" mb={2}>
                    <Text fontWeight="bold">{rec.name}</Text>
                    <Badge colorScheme={rec.confidence > 0.7 ? 'green' : 'yellow'}>
                      {Math.round(rec.confidence * 100)}% confidence
                    </Badge>
                  </HStack>
                  <Text fontSize="sm" mb={2}>{rec.description}</Text>
                  {rec.subdomain_ids.length > 0 && (
                    <Box>
                      <Text fontSize="sm" fontWeight="bold">Subdomains:</Text>
                      <HStack wrap="wrap">
                        {rec.subdomain_ids.map((sub) => (
                          <Tag key={sub} size="sm" colorScheme="blue">
                            <TagLabel>{sub}</TagLabel>
                          </Tag>
                        ))}
                      </HStack>
                    </Box>
                  )}
                  <Text fontSize="xs" color="gray.600" mt={2}>{rec.reasoning}</Text>
                </Box>
              ))}
            </VStack>
          </ModalBody>
          <ModalFooter>
            <ButtonGroup>
              <Button variant="ghost" onClick={onRecommendationsClose}>Cancel</Button>
              <Button colorScheme="blue" onClick={applyDomainRecommendations}>
                Apply Recommendations
              </Button>
            </ButtonGroup>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Progress Section */}
      {(isAnalyzing || progress.status === 'completed') && (
        <Box borderWidth={1} borderRadius="lg" p={4}>
          <Text mb={2}>Analysis Progress</Text>
          <Progress
            value={(progress.analyzed_files / Math.max(progress.total_files, 1)) * 100}
            size="sm"
            colorScheme={progress.status === 'completed' ? 'green' : 'blue'}
          />
          <Text mt={2} fontSize="sm">
            {progress.analyzed_files} / {progress.total_files} files analyzed
            {progress.current_file && ` (Current: ${progress.current_file})`}
          </Text>
        </Box>
      )}

      {/* Results Section */}
      {isLoadingCache ? (
        <Center p={8}>
          <Spinner />
        </Center>
      ) : (
        Object.entries(resultsByDomain).map(([domain, files]) => (
          <Box key={domain} borderWidth={1} borderRadius="lg" p={4}>
            <Accordion allowMultiple>
              <AccordionItem>
                <AccordionButton>
                  <Box flex="1" textAlign="left">
                    <Text fontWeight="bold">
                      {domain} ({files.length} files)
                    </Text>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel>
                  <VStack align="stretch" spacing={4}>
                    {files.map(({ filePath, ...analysis }) => (
                      <Box key={filePath} p={4} borderWidth={1} borderRadius="md">
                        <HStack justify="space-between" mb={2}>
                          <Text fontWeight="bold">{filePath}</Text>
                          <Checkbox
                            isChecked={selectedFiles.includes(filePath)}
                            onChange={() => toggleFileSelection(filePath)}
                          >
                            Select for reanalysis
                          </Checkbox>
                        </HStack>
                        <VStack align="stretch" spacing={3}>
                          <Box>
                            <Text fontWeight="semibold">Purpose:</Text>
                            <Text>{analysis.purpose}</Text>
                          </Box>
                          
                          <Box>
                            <Text fontWeight="semibold">Key Functionality:</Text>
                            <List styleType="disc" pl={4}>
                              {analysis.key_functionality.map((item, idx) => (
                                <ListItem key={idx}>{item}</ListItem>
                              ))}
                            </List>
                          </Box>
                          
                          <Box>
                            <Text fontWeight="semibold">Dependencies:</Text>
                            <List styleType="disc" pl={4}>
                              {analysis.dependencies.map((item, idx) => (
                                <ListItem key={idx}>{item}</ListItem>
                              ))}
                            </List>
                          </Box>
                          
                          <Box>
                            <Text fontWeight="semibold">Implementation Details:</Text>
                            <List styleType="disc" pl={4}>
                              {analysis.implementation_details.map((item, idx) => (
                                <ListItem key={idx}>{item}</ListItem>
                              ))}
                            </List>
                          </Box>
                          
                          <Box>
                            <Text fontWeight="semibold">Potential Issues:</Text>
                            <List styleType="disc" pl={4}>
                              {analysis.potential_issues.map((item, idx) => (
                                <ListItem key={idx}>{item}</ListItem>
                              ))}
                            </List>
                          </Box>
                          
                          {analysis.functions && analysis.functions.length > 0 && (
                            <Box>
                              <Text fontWeight="semibold">Functions:</Text>
                              <Accordion allowMultiple>
                                {analysis.functions.map((func, idx) => (
                                  <AccordionItem key={idx}>
                                    <AccordionButton>
                                      <Box flex="1" textAlign="left">
                                        <Text fontWeight="medium">{func.name}</Text>
                                      </Box>
                                      <AccordionIcon />
                                    </AccordionButton>
                                    <AccordionPanel>
                                      <VStack align="stretch" spacing={2}>
                                        <Text><strong>Line:</strong> {func.line_number}</Text>
                                        <Text><strong>Description:</strong> {func.description}</Text>
                                        {func.parameters.length > 0 && (
                                          <Box>
                                            <Text><strong>Parameters:</strong></Text>
                                            <List styleType="disc" pl={4}>
                                              {func.parameters.map((param, pidx) => (
                                                <ListItem key={pidx}>{param}</ListItem>
                                              ))}
                                            </List>
                                          </Box>
                                        )}
                                        {func.return_type && (
                                          <Text><strong>Return Type:</strong> {func.return_type}</Text>
                                        )}
                                      </VStack>
                                    </AccordionPanel>
                                  </AccordionItem>
                                ))}
                              </Accordion>
                            </Box>
                          )}
                        </VStack>
                      </Box>
                    ))}
                  </VStack>
                </AccordionPanel>
              </AccordionItem>
            </Accordion>
          </Box>
        ))
      )}
    </VStack>
  );
};

export default CodeAnalyzer; 