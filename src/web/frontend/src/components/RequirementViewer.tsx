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
import remarkGfm from 'remark-gfm';
import MarkdownRenderer from './MarkdownRenderer';

interface CodeReference {
  file: string;
  line: number;
  function: string;
  type: string;
  url: string;
}

interface Requirement {
  id: string;
  domain: string;
  description: string;
  linked_blocks: string[];
  content: string;
  code_references: CodeReference[];
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
  const linkColor = useColorModeValue('blue.500', 'blue.300');

  const handleCodeLinkClick = (url: string) => {
    window.open(url, '_blank');
  };

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
                Code References
              </Heading>
              <VStack align="stretch" spacing={2}>
                {requirement.code_references?.map((ref, index) => (
                  <Box 
                    key={index}
                    p={2}
                    borderWidth="1px"
                    borderRadius="md"
                    borderColor={borderColor}
                    _hover={{ bg: bgColor, cursor: 'pointer' }}
                    onClick={() => handleCodeLinkClick(ref.url)}
                  >
                    <Text color={linkColor} fontWeight="medium">
                      {ref.file}:{ref.line} - {ref.function}
                    </Text>
                    <Text fontSize="sm" color="gray.500">
                      Type: {ref.type}
                    </Text>
                  </Box>
                ))}
                {(!requirement.code_references || requirement.code_references.length === 0) && (
                  <Text color="gray.500" fontSize="sm">
                    No code references available
                  </Text>
                )}
              </VStack>
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
                <ReactMarkdown
                  components={MarkdownRenderer}
                  remarkPlugins={[remarkGfm]}
                >
                  {requirement.content}
                </ReactMarkdown>
              </Box>
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