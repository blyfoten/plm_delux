import React, { useEffect, useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Input,
  Select,
  VStack,
  HStack,
  Text,
  Box,
  Tag,
  TagLabel,
  TagCloseButton,
  IconButton,
  Textarea,
  FormControl,
  FormLabel,
} from '@chakra-ui/react';
import { AddIcon, CloseIcon } from '@chakra-ui/icons';

interface DomainConfig {
  name: string;
  description: string;
  parent_domain?: string;
  subdomain_ids: string[];
}

interface PLMSettings {
  source_folder: string;
  requirements_folder: string;
  architecture_folder: string;
  folder_structure: 'hierarchical' | 'flat';
  preferred_languages: string[];
  custom_llm_instructions: string;
  source_include_patterns: string[];
  source_exclude_patterns: string[];
  domains: Record<string, DomainConfig>;
}

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: (() => void) | undefined;
  onSave: () => void;
  forceConfiguration?: boolean;
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({ 
  isOpen, 
  onClose, 
  onSave,
  forceConfiguration = false 
}) => {
  const [settings, setSettings] = useState<PLMSettings>({
    source_folder: '',
    requirements_folder: '',
    architecture_folder: '',
    folder_structure: 'hierarchical',
    preferred_languages: [],
    custom_llm_instructions: '',
    source_include_patterns: [],
    source_exclude_patterns: [],
    domains: {},
  });
  const [newLanguage, setNewLanguage] = useState('');
  const [newIncludePattern, setNewIncludePattern] = useState('');
  const [newExcludePattern, setNewExcludePattern] = useState('');
  const [newDomainId, setNewDomainId] = useState('');
  const [newDomainName, setNewDomainName] = useState('');
  const [newDomainDescription, setNewDomainDescription] = useState('');
  const [newDomainParent, setNewDomainParent] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetch('http://localhost:8000/api/settings')
        .then((response) => response.json())
        .then((data) => setSettings(data))
        .catch((error) => console.error('Error loading settings:', error));
    }
  }, [isOpen]);

  const handleSave = async () => {
    try {
      await fetch('http://localhost:8000/api/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });
      onSave();
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  const handleAddLanguage = () => {
    if (newLanguage && !settings.preferred_languages.includes(newLanguage)) {
      setSettings({
        ...settings,
        preferred_languages: [...settings.preferred_languages, newLanguage],
      });
      setNewLanguage('');
    }
  };

  const handleAddIncludePattern = () => {
    if (newIncludePattern && !settings.source_include_patterns.includes(newIncludePattern)) {
      setSettings({
        ...settings,
        source_include_patterns: [...settings.source_include_patterns, newIncludePattern],
      });
      setNewIncludePattern('');
    }
  };

  const handleAddExcludePattern = () => {
    if (newExcludePattern && !settings.source_exclude_patterns.includes(newExcludePattern)) {
      setSettings({
        ...settings,
        source_exclude_patterns: [...settings.source_exclude_patterns, newExcludePattern],
      });
      setNewExcludePattern('');
    }
  };

  const handleAddDomain = () => {
    if (newDomainId && !settings.domains[newDomainId]) {
      setSettings({
        ...settings,
        domains: {
          ...settings.domains,
          [newDomainId]: {
            name: newDomainName || newDomainId,
            description: newDomainDescription,
            parent_domain: newDomainParent || undefined,
            subdomain_ids: [],
          },
        },
      });
      if (newDomainParent && settings.domains[newDomainParent]) {
        setSettings((prev) => ({
          ...prev,
          domains: {
            ...prev.domains,
            [newDomainParent]: {
              ...prev.domains[newDomainParent],
              subdomain_ids: [...prev.domains[newDomainParent].subdomain_ids, newDomainId],
            },
          },
        }));
      }
      setNewDomainId('');
      setNewDomainName('');
      setNewDomainDescription('');
      setNewDomainParent('');
    }
  };

  const handleRemoveDomain = (domainId: string) => {
    const { [domainId]: removedDomain, ...remainingDomains } = settings.domains;
    
    if (removedDomain.parent_domain) {
      const parentDomain = settings.domains[removedDomain.parent_domain];
      if (parentDomain) {
        remainingDomains[removedDomain.parent_domain] = {
          ...parentDomain,
          subdomain_ids: parentDomain.subdomain_ids.filter(id => id !== domainId),
        };
      }
    }
    
    Object.keys(remainingDomains).forEach(id => {
      if (remainingDomains[id].parent_domain === domainId) {
        remainingDomains[id] = {
          ...remainingDomains[id],
          parent_domain: undefined,
        };
      }
    });

    setSettings({
      ...settings,
      domains: remainingDomains,
    });
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose || (() => {})} 
      size="xl"
      closeOnOverlayClick={!forceConfiguration}
      closeOnEsc={!forceConfiguration}
    >
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          {forceConfiguration ? 'Initial Configuration Required' : 'PLM Settings'}
        </ModalHeader>
        {!forceConfiguration && <ModalCloseButton />}
        <ModalBody>
          {forceConfiguration && (
            <Box mb={6} p={4} bg="blue.50" borderRadius="md">
              <Text>
                Please configure your initial settings before continuing. 
                These settings are required for the application to function properly.
              </Text>
            </Box>
          )}
          
          <VStack spacing={6} align="stretch">
            <Box>
              <Text fontWeight="bold" mb={2}>Folder Paths</Text>
              <VStack spacing={4}>
                <FormControl>
                  <FormLabel>Source Folder</FormLabel>
                  <Input
                    value={settings.source_folder}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                      setSettings({ ...settings, source_folder: e.target.value })}
                  />
                  <Text fontSize="sm" color="gray.600" mt={1}>
                    Used for both input (code analysis) and output (generated code)
                  </Text>
                </FormControl>
                <FormControl>
                  <FormLabel>Requirements Folder</FormLabel>
                  <Input
                    value={settings.requirements_folder}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                      setSettings({ ...settings, requirements_folder: e.target.value })}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Architecture Folder</FormLabel>
                  <Input
                    value={settings.architecture_folder}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                      setSettings({ ...settings, architecture_folder: e.target.value })}
                  />
                </FormControl>
              </VStack>
            </Box>

            <Box>
              <Text fontWeight="bold" mb={2}>Folder Structure</Text>
              <Select
                value={settings.folder_structure}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => 
                  setSettings({ ...settings, folder_structure: e.target.value as 'hierarchical' | 'flat' })}
              >
                <option value="hierarchical">Hierarchical</option>
                <option value="flat">Flat</option>
              </Select>
            </Box>

            <Box>
              <Text fontWeight="bold" mb={2}>Preferred Languages</Text>
              <Box mb={2}>
                {settings.preferred_languages.map((lang) => (
                  <Tag key={lang} size="md" borderRadius="full" variant="solid" colorScheme="blue" mr={2} mb={2}>
                    <TagLabel>{lang}</TagLabel>
                    <TagCloseButton
                      onClick={() => setSettings({
                        ...settings,
                        preferred_languages: settings.preferred_languages.filter((l) => l !== lang),
                      })}
                    />
                  </Tag>
                ))}
              </Box>
              <HStack>
                <Input
                  placeholder="Add language..."
                  value={newLanguage}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewLanguage(e.target.value)}
                />
                <IconButton
                  aria-label="Add language"
                  icon={<AddIcon />}
                  onClick={handleAddLanguage}
                />
              </HStack>
            </Box>

            <Box>
              <Text fontWeight="bold" mb={2}>Custom LLM Instructions</Text>
              <Textarea
                value={settings.custom_llm_instructions}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                  setSettings({ ...settings, custom_llm_instructions: e.target.value })}
                rows={4}
              />
            </Box>

            <Box>
              <Text fontWeight="bold" mb={2}>Source Include Patterns</Text>
              <Box mb={2}>
                {settings.source_include_patterns.map((pattern) => (
                  <Tag key={pattern} size="md" borderRadius="full" variant="solid" colorScheme="green" mr={2} mb={2}>
                    <TagLabel>{pattern}</TagLabel>
                    <TagCloseButton
                      onClick={() => setSettings({
                        ...settings,
                        source_include_patterns: settings.source_include_patterns.filter((p) => p !== pattern),
                      })}
                    />
                  </Tag>
                ))}
              </Box>
              <HStack>
                <Input
                  placeholder="Add include pattern..."
                  value={newIncludePattern}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewIncludePattern(e.target.value)}
                />
                <IconButton
                  aria-label="Add include pattern"
                  icon={<AddIcon />}
                  onClick={handleAddIncludePattern}
                />
              </HStack>
            </Box>

            <Box>
              <Text fontWeight="bold" mb={2}>Source Exclude Patterns</Text>
              <Box mb={2}>
                {settings.source_exclude_patterns.map((pattern) => (
                  <Tag key={pattern} size="md" borderRadius="full" variant="solid" colorScheme="red" mr={2} mb={2}>
                    <TagLabel>{pattern}</TagLabel>
                    <TagCloseButton
                      onClick={() => setSettings({
                        ...settings,
                        source_exclude_patterns: settings.source_exclude_patterns.filter((p) => p !== pattern),
                      })}
                    />
                  </Tag>
                ))}
              </Box>
              <HStack>
                <Input
                  placeholder="Add exclude pattern..."
                  value={newExcludePattern}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewExcludePattern(e.target.value)}
                />
                <IconButton
                  aria-label="Add exclude pattern"
                  icon={<AddIcon />}
                  onClick={handleAddExcludePattern}
                />
              </HStack>
            </Box>

            <Box>
              <Text fontWeight="bold" mb={2}>Domains</Text>
              <VStack spacing={4} align="stretch">
                {Object.entries(settings.domains).map(([domainId, domain]) => (
                  <Box key={domainId} p={3} borderWidth="1px" borderRadius="md">
                    <HStack justify="space-between" mb={2}>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="semibold">{domain.name} ({domainId})</Text>
                        <Text fontSize="sm" color="gray.600">{domain.description}</Text>
                        {domain.parent_domain && (
                          <Text fontSize="sm">Parent: {domain.parent_domain}</Text>
                        )}
                        {domain.subdomain_ids.length > 0 && (
                          <Text fontSize="sm">
                            Subdomains: {domain.subdomain_ids.join(', ')}
                          </Text>
                        )}
                      </VStack>
                      <IconButton
                        aria-label="Remove domain"
                        icon={<CloseIcon />}
                        size="sm"
                        onClick={() => handleRemoveDomain(domainId)}
                      />
                    </HStack>
                  </Box>
                ))}

                <Box p={3} borderWidth="1px" borderRadius="md">
                  <Text fontWeight="semibold" mb={2}>Add New Domain</Text>
                  <VStack spacing={3}>
                    <FormControl>
                      <FormLabel>Domain ID</FormLabel>
                      <Input
                        placeholder="e.g., ui, backend"
                        value={newDomainId}
                        onChange={(e) => setNewDomainId(e.target.value)}
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>Name</FormLabel>
                      <Input
                        placeholder="e.g., User Interface"
                        value={newDomainName}
                        onChange={(e) => setNewDomainName(e.target.value)}
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>Description</FormLabel>
                      <Input
                        placeholder="Domain description..."
                        value={newDomainDescription}
                        onChange={(e) => setNewDomainDescription(e.target.value)}
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>Parent Domain (optional)</FormLabel>
                      <Select
                        value={newDomainParent}
                        onChange={(e) => setNewDomainParent(e.target.value)}
                        placeholder="Select parent domain"
                      >
                        {Object.keys(settings.domains).map((domainId) => (
                          <option key={domainId} value={domainId}>
                            {settings.domains[domainId].name}
                          </option>
                        ))}
                      </Select>
                    </FormControl>
                    <Button
                      leftIcon={<AddIcon />}
                      onClick={handleAddDomain}
                      colorScheme="blue"
                      width="full"
                    >
                      Add Domain
                    </Button>
                  </VStack>
                </Box>
              </VStack>
            </Box>
          </VStack>
        </ModalBody>
        <ModalFooter>
          {!forceConfiguration && (
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
          )}
          <Button colorScheme="blue" onClick={handleSave}>
            {forceConfiguration ? 'Save and Continue' : 'Save'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}; 