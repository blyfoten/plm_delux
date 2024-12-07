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
  Box,
  Text,
  Badge,
  VStack,
  Divider,
  Heading,
  useColorModeValue,
} from '@chakra-ui/react';
import ReactMarkdown from 'react-markdown';
import ChakraUIRenderer from 'chakra-ui-markdown-renderer';

interface Requirement {
  id: string;
  domain: string;
  description: string;
  linked_blocks: string[];
  content: string;
}

interface RequirementViewerProps {
  isOpen: boolean;
  onClose: () => void;
  requirement: Requirement;
  onEdit?: () => void;
}

const RequirementViewer: React.FC<RequirementViewerProps> = ({
  isOpen,
  onClose,
  requirement,
  onEdit,
}) => {
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <Text>{requirement.id}</Text>
          <Badge colorScheme="blue" mt={1}>
            {requirement.domain}
          </Badge>
        </ModalHeader>
        <ModalCloseButton />

        <ModalBody>
          <VStack spacing={4} align="stretch">
            <Box>
              <Heading size="sm" mb={2}>
                Description
              </Heading>
              <Text>{requirement.description}</Text>
            </Box>

            <Divider />

            <Box>
              <Heading size="sm" mb={2}>
                Linked Blocks
              </Heading>
              <Box>
                {requirement.linked_blocks.map((blockId) => (
                  <Badge key={blockId} mr={2} mb={2} colorScheme="green">
                    {blockId}
                  </Badge>
                ))}
              </Box>
            </Box>

            <Divider />

            <Box>
              <Heading size="sm" mb={2}>
                Content
              </Heading>
              <Box
                p={4}
                bg={bgColor}
                borderRadius="md"
                borderWidth="1px"
                borderColor={borderColor}
              >
                <ReactMarkdown components={ChakraUIRenderer()} skipHtml>
                  {requirement.content}
                </ReactMarkdown>
              </Box>
            </Box>

            <Box>
              <Heading size="sm" mb={2}>
                Implementation Status
              </Heading>
              <Badge colorScheme="yellow">In Progress</Badge>
            </Box>
          </VStack>
        </ModalBody>

        <ModalFooter>
          {onEdit && (
            <Button colorScheme="blue" mr={3} onClick={onEdit}>
              Edit
            </Button>
          )}
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default RequirementViewer; 