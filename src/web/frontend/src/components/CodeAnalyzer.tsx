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
} from '@chakra-ui/react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

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

  return (
    <VStack spacing={6} align="stretch" height="100%">
      <HStack justify="space-between">
        <Heading size="md">Code Analysis</Heading>
        <ButtonGroup>
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
                        <Text>{analysis.purpose}</Text>
                        {/* ... rest of the analysis display ... */}
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