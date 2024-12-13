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
import { AddIcon } from '@chakra-ui/icons';

interface PLMSettings {
  source_folder: string;
  requirements_folder: string;
  architecture_folder: string;
  generated_folder: string;
  folder_structure: 'hierarchical' | 'flat';
  preferred_languages: string[];
  custom_llm_instructions: string;
  source_include_patterns: string[];
  source_exclude_patterns: string[];
}

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({ isOpen, onClose }) => {
  const [settings, setSettings] = useState<PLMSettings>({
    source_folder: '',
    requirements_folder: '',
    architecture_folder: '',
    generated_folder: '',
    folder_structure: 'hierarchical',
    preferred_languages: [],
    custom_llm_instructions: '',
    source_include_patterns: [],
    source_exclude_patterns: [],
  });
  const [newLanguage, setNewLanguage] = useState('');
  const [newIncludePattern, setNewIncludePattern] = useState('');
  const [newExcludePattern, setNewExcludePattern] = useState('');

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
      onClose();
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

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>PLM Settings</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
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
                <FormControl>
                  <FormLabel>Generated Folder</FormLabel>
                  <Input
                    value={settings.generated_folder}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                      setSettings({ ...settings, generated_folder: e.target.value })}
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
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button colorScheme="blue" onClick={handleSave}>
            Save
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}; 