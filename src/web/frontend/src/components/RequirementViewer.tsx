import React from 'react';
import {
  Box,
  VStack,
  Text,
  Heading,
  Link,
  UnorderedList,
  ListItem,
  Divider,
  Card,
  CardBody,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  Button,
  HStack,
} from '@chakra-ui/react';
import ReactMarkdown from 'react-markdown';

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
  additional_notes: string[];
  implementation_files: string[];
  code_references: CodeReference[];
  content?: string;
}

interface RequirementViewerProps {
  requirement: Requirement;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: () => void;
}

const RequirementViewer: React.FC<RequirementViewerProps> = ({
  requirement,
  isOpen,
  onClose,
  onEdit
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Requirement {requirement.id}</ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack align="stretch" spacing={4}>
            <Box>
              <Heading as="h2" size="md" color="blue.500" mb={2}>
                {requirement.domain}
              </Heading>
              <Text fontSize="lg" fontWeight="medium">
                {requirement.description}
              </Text>
            </Box>

            <Divider />

            {requirement.additional_notes.length > 0 && (
              <Box>
                <Heading as="h3" size="sm" mb={2}>
                  Additional Notes
                </Heading>
                <UnorderedList spacing={1}>
                  {requirement.additional_notes.map((note, index) => (
                    <ListItem key={index}>
                      <Text>{note}</Text>
                    </ListItem>
                  ))}
                </UnorderedList>
              </Box>
            )}

            {requirement.implementation_files.length > 0 && (
              <Box>
                <Heading as="h3" size="sm" mb={2}>
                  Implementation Files
                </Heading>
                <UnorderedList spacing={1}>
                  {requirement.implementation_files.map((file, index) => (
                    <ListItem key={index}>
                      <Text>{file}</Text>
                    </ListItem>
                  ))}
                </UnorderedList>
              </Box>
            )}

            {requirement.linked_blocks.length > 0 && (
              <Box>
                <Heading as="h3" size="sm" mb={2}>
                  Linked Blocks
                </Heading>
                <UnorderedList spacing={1}>
                  {requirement.linked_blocks.map((block, index) => (
                    <ListItem key={index}>
                      <Text>{block}</Text>
                    </ListItem>
                  ))}
                </UnorderedList>
              </Box>
            )}

            {requirement.code_references?.length > 0 && (
              <Box>
                <Heading as="h3" size="sm" mb={2}>
                  Code References
                </Heading>
                <UnorderedList spacing={1}>
                  {requirement.code_references.map((ref, index) => (
                    <ListItem key={index}>
                      <Link 
                        href={ref.url.replace(/'/g, '"').replace(/ /g, '')} 
                        isExternal 
                        color="blue.500">
                        {ref.file}:{ref.line}
                      </Link>
                      {ref.function && ` (${ref.function})`}
                    </ListItem>
                  ))}
                </UnorderedList>
              </Box>
            )}

            {requirement.content && (
              <Box mt={4}>
                <Heading as="h3" size="sm" mb={2}>
                  Content
                </Heading>
                <Box 
                  p={4} 
                  bg="gray.50" 
                  borderRadius="md"
                  sx={{
                    'pre': { whiteSpace: 'pre-wrap', wordBreak: 'break-word' }
                  }}
                >
                  <ReactMarkdown>
                    {requirement.content}
                  </ReactMarkdown>
                </Box>
              </Box>
            )}
          </VStack>

          <HStack justify="flex-end" mt={6}>
            {onEdit && (
              <Button colorScheme="blue" onClick={onEdit}>
                Edit
              </Button>
            )}
            <Button onClick={onClose}>Close</Button>
          </HStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default RequirementViewer; 