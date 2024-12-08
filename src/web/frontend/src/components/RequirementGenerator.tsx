import React from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
  useToast,
  Select,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';

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

  return (
    <Box p={4} borderWidth="1px" borderRadius="lg">
      <form onSubmit={handleSubmit(onSubmit)}>
        <VStack spacing={4}>
          <FormControl>
            <FormLabel>Domain</FormLabel>
            <Select {...register('domain')} placeholder="Select domain">
              <option value="ui">User Interface</option>
              <option value="motor_and_doors">Motor and Doors</option>
              <option value="offboard">Offboard Systems</option>
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