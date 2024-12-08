import React from 'react';
import {
  Text,
  Heading,
  UnorderedList,
  OrderedList,
  ListItem,
  Code,
  Link,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Box,
} from '@chakra-ui/react';
import { Components } from 'react-markdown';

const MarkdownRenderer: Components = {
  h1: ({ children }) => (
    <Heading as="h1" size="xl" my={4}>
      {children}
    </Heading>
  ),
  h2: ({ children }) => (
    <Heading as="h2" size="lg" my={3}>
      {children}
    </Heading>
  ),
  h3: ({ children }) => (
    <Heading as="h3" size="md" my={2}>
      {children}
    </Heading>
  ),
  p: ({ children }) => <Text my={2}>{children}</Text>,
  ul: ({ children }) => <UnorderedList my={2}>{children}</UnorderedList>,
  ol: ({ children }) => <OrderedList my={2}>{children}</OrderedList>,
  li: ({ children }) => <ListItem>{children}</ListItem>,
  code: ({ inline, children }) =>
    inline ? (
      <Code px={2} py={1}>
        {children}
      </Code>
    ) : (
      <Box
        as="pre"
        p={4}
        bg="gray.50"
        borderRadius="md"
        overflowX="auto"
        my={4}
      >
        <Code display="block" whiteSpace="pre">
          {children}
        </Code>
      </Box>
    ),
  a: ({ href, children }) => (
    <Link color="blue.500" href={href} isExternal>
      {children}
    </Link>
  ),
  table: ({ children }) => (
    <Table variant="simple" my={4}>
      {children}
    </Table>
  ),
  thead: ({ children }) => <Thead>{children}</Thead>,
  tbody: ({ children }) => <Tbody>{children}</Tbody>,
  tr: ({ children }) => <Tr>{children}</Tr>,
  th: ({ children }) => <Th>{children}</Th>,
  td: ({ children }) => <Td>{children}</Td>,
  blockquote: ({ children }) => (
    <Box
      borderLeft="4px"
      borderColor="gray.200"
      pl={4}
      my={4}
      color="gray.600"
    >
      {children}
    </Box>
  ),
  hr: () => <Box as="hr" my={6} borderColor="gray.200" />,
};

export default MarkdownRenderer; 