import React from 'react';
import {
  Box,
  VStack,
  Text,
  Badge,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Button,
  useDisclosure,
} from '@chakra-ui/react';
import RequirementEditor from './RequirementEditor';

interface Requirement {
  id: string;
  domain: string;
  description: string;
  linked_blocks: string[];
  content: string;
}

interface RequirementsListProps {
  requirements: Record<string, Requirement>;
  onRequirementSelect: (requirement: Requirement) => void;
  onRequirementUpdate?: (requirement: Requirement) => void;
}

const RequirementsList: React.FC<RequirementsListProps> = ({
  requirements,
  onRequirementSelect,
  onRequirementUpdate,
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedRequirement, setSelectedRequirement] = React.useState<Requirement | null>(null);

  const handleEditClick = (requirement: Requirement) => {
    setSelectedRequirement(requirement);
    onOpen();
  };

  const handleRequirementUpdate = (updatedRequirement: Requirement) => {
    onRequirementUpdate?.(updatedRequirement);
    onClose();
  };

  const groupedRequirements = React.useMemo(() => {
    const groups: Record<string, Requirement[]> = {};
    if (requirements) {
      Object.values(requirements).forEach((req) => {
        if (!groups[req.domain]) {
          groups[req.domain] = [];
        }
        groups[req.domain].push(req);
      });
    }
    return groups;
  }, [requirements]);

  if (!requirements || Object.keys(requirements).length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Text color="gray.500">No requirements found</Text>
      </Box>
    );
  }

  return (
    <Box>
      <Accordion allowMultiple>
        {Object.entries(groupedRequirements).map(([domain, reqs]) => (
          <AccordionItem key={domain}>
            <AccordionButton>
              <Box flex="1" textAlign="left">
                <Text fontWeight="bold">{domain}</Text>
                <Badge ml={2} colorScheme="blue">
                  {reqs.length}
                </Badge>
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel>
              <VStack align="stretch" spacing={4}>
                {reqs.map((req) => (
                  <Box
                    key={req.id}
                    p={4}
                    borderWidth="1px"
                    borderRadius="md"
                    _hover={{ bg: 'gray.50' }}
                  >
                    <Text fontWeight="semibold">{req.id}</Text>
                    <Text fontSize="sm" color="gray.600" mb={2}>
                      {req.description}
                    </Text>
                    <Box mb={2}>
                      {req.linked_blocks.map((blockId) => (
                        <Badge key={blockId} mr={2} colorScheme="green">
                          {blockId}
                        </Badge>
                      ))}
                    </Box>
                    <Button
                      size="sm"
                      colorScheme="blue"
                      mr={2}
                      onClick={() => onRequirementSelect(req)}
                    >
                      View
                    </Button>
                    <Button
                      size="sm"
                      colorScheme="teal"
                      onClick={() => handleEditClick(req)}
                    >
                      Edit
                    </Button>
                  </Box>
                ))}
              </VStack>
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>

      {selectedRequirement && (
        <RequirementEditor
          isOpen={isOpen}
          onClose={onClose}
          requirement={selectedRequirement}
          onSave={handleRequirementUpdate}
        />
      )}
    </Box>
  );
};

export default RequirementsList; 