import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Textarea,
  VStack,
  useToast,
  Select,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';

interface DomainConfig {
  name: string;
  description: string;
  parent_domain?: string;
  subdomain_ids: string[];
}

interface RequirementGeneratorProps {
  onRequirementsGenerated: () => void;
}

interface FormData {
  domain: string;
  context: string;
}

const RequirementGenerator: React.FC<RequirementGeneratorProps> = ({
  onRequirementsGenerated,
}) => {
  const { register, handleSubmit, formState: { isSubmitting }, reset } = useForm<FormData>();
  const toast = useToast();
  const [domains, setDomains] = useState<Record<string, DomainConfig>>({});

  useEffect(() => {
    // Load domains from settings
    fetch('http://localhost:8000/api/settings')
      .then((response) => response.json())
      .then((data) => setDomains(data.domains))
      .catch((error) => console.error('Error loading domains:', error));
  }, []);

  const onSubmit = async (data: FormData) => {
    try {
      const response = await fetch('http://localhost:8000/api/requirements/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to generate requirements');
      }

      const result = await response.json();
      
      // Reset the form
      reset();
      
      // Notify success
      toast({
        title: 'Requirements Generated',
        description: `Generated ${result.requirements.length} requirements`,
        status: 'success',
        duration: 5000,
      });

      // Refresh the requirements list
      onRequirementsGenerated();
      
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    }
  };

  // Function to get domain display name
  const getDomainDisplayName = (domainId: string) => {
    const domain = domains[domainId];
    return domain ? `${domain.name} (${domainId})` : domainId;
  };

  // Function to get domain hierarchy
  const getDomainHierarchy = (domainId: string, level: number = 0): JSX.Element[] => {
    const domain = domains[domainId];
    if (!domain) return [];

    const elements: JSX.Element[] = [
      <option key={domainId} value={domainId}>
        {"  ".repeat(level)}
        {getDomainDisplayName(domainId)}
      </option>
    ];

    // Add subdomains recursively
    if (domain.subdomain_ids) {
      domain.subdomain_ids.forEach(subId => {
        elements.push(...getDomainHierarchy(subId, level + 1));
      });
    }

    return elements;
  };

  // Get root domains (domains without parents)
  const getRootDomains = () => {
    return Object.keys(domains).filter(id => !domains[id].parent_domain);
  };

  return (
    <Box p={4} borderWidth="1px" borderRadius="lg">
      <form onSubmit={handleSubmit(onSubmit)}>
        <VStack spacing={4}>
          <FormControl>
            <FormLabel>Domain</FormLabel>
            <Select {...register('domain')} placeholder="Select domain">
              {getRootDomains().map(domainId => getDomainHierarchy(domainId))}
            </Select>
          </FormControl>

          <FormControl>
            <FormLabel>Context</FormLabel>
            <Textarea
              {...register('context')}
              placeholder="Describe what you want to generate requirements for..."
              rows={4}
            />
          </FormControl>

          <Button
            type="submit"
            colorScheme="blue"
            isLoading={isSubmitting}
            loadingText="Generating..."
            width="full"
          >
            Generate Requirements
          </Button>
        </VStack>
      </form>
    </Box>
  );
};

export default RequirementGenerator; 