import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
  Box,
  useToast,
  Tag,
  TagLabel,
  TagCloseButton,
  HStack,
  Select,
} from '@chakra-ui/react';
import { useForm, Controller } from 'react-hook-form';

interface Requirement {
  id: string;
  domain: string;
  description: string;
  linked_blocks: string[];
  content: string;
}

interface RequirementEditorProps {
  isOpen: boolean;
  onClose: () => void;
  requirement: Requirement;
  onSave: (requirement: Requirement) => void;
}

const RequirementEditor: React.FC<RequirementEditorProps> = ({
  isOpen,
  onClose,
  requirement,
  onSave,
}) => {
  const toast = useToast();
  const { control, handleSubmit, watch, setValue } = useForm<Requirement>({
    defaultValues: requirement,
  });
  const [newBlock, setNewBlock] = React.useState('');
  const [availableBlocks, setAvailableBlocks] = React.useState<string[]>([]);

  // Fetch available blocks when the modal opens
  React.useEffect(() => {
    if (isOpen) {
      fetchAvailableBlocks();
    }
  }, [isOpen]);

  const fetchAvailableBlocks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/architecture');
      const data = await response.json();
      const blocks = extractBlockIds(data);
      setAvailableBlocks(blocks);
    } catch (error) {
      console.error('Error fetching blocks:', error);
    }
  };

  const extractBlockIds = (architecture: any): string[] => {
    const blocks: string[] = [];
    const processBlock = (block: any) => {
      blocks.push(block.block_id);
      block.subblocks?.forEach((subblock: any) => processBlock(subblock));
    };
    processBlock(architecture);
    return blocks;
  };

  const onSubmit = async (data: Requirement) => {
    try {
      await onSave(data);
      toast({
        title: 'Requirement updated',
        status: 'success',
        duration: 3000,
      });
      onClose();
    } catch (error) {
      toast({
        title: 'Error updating requirement',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleAddBlock = () => {
    if (newBlock && !watch('linked_blocks').includes(newBlock)) {
      setValue('linked_blocks', [...watch('linked_blocks'), newBlock]);
      setNewBlock('');
    }
  };

  const handleRemoveBlock = (blockId: string) => {
    setValue(
      'linked_blocks',
      watch('linked_blocks').filter((id) => id !== blockId)
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Edit Requirement {requirement.id}</ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            <VStack spacing={4}>
              <Controller
                name="domain"
                control={control}
                render={({ field }) => (
                  <FormControl>
                    <FormLabel>Domain</FormLabel>
                    <Input {...field} />
                  </FormControl>
                )}
              />

              <Controller
                name="description"
                control={control}
                render={({ field }) => (
                  <FormControl>
                    <FormLabel>Description</FormLabel>
                    <Textarea {...field} rows={3} />
                  </FormControl>
                )}
              />

              <FormControl>
                <FormLabel>Linked Blocks</FormLabel>
                <HStack mb={2}>
                  <Select
                    value={newBlock}
                    onChange={(e) => setNewBlock(e.target.value)}
                    placeholder="Select a block"
                  >
                    {availableBlocks.map((blockId) => (
                      <option key={blockId} value={blockId}>
                        {blockId}
                      </option>
                    ))}
                  </Select>
                  <Button onClick={handleAddBlock}>Add</Button>
                </HStack>
                <Box>
                  {watch('linked_blocks').map((blockId) => (
                    <Tag
                      key={blockId}
                      size="md"
                      borderRadius="full"
                      variant="solid"
                      colorScheme="green"
                      m={1}
                    >
                      <TagLabel>{blockId}</TagLabel>
                      <TagCloseButton onClick={() => handleRemoveBlock(blockId)} />
                    </Tag>
                  ))}
                </Box>
              </FormControl>

              <Controller
                name="content"
                control={control}
                render={({ field }) => (
                  <FormControl>
                    <FormLabel>Content</FormLabel>
                    <Textarea {...field} rows={10} />
                  </FormControl>
                )}
              />
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" type="submit">
              Save
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
};

export default RequirementEditor; 