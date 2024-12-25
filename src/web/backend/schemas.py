"""JSON schemas for data validation."""

from typing import Dict, Any

# Schema for function information
FUNCTION_INFO_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "line": {"type": "integer", "minimum": 0},
        "description": {"type": "string"},
        "parameters": {
            "type": "array",
            "items": {"type": "string"}
        },
        "return_type": {"type": ["string", "null"]}
    },
    "required": ["name", "line", "description"]
}

# Schema for file analysis
FILE_ANALYSIS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "purpose": {"type": "string"},
        "key_functionality": {
            "type": "array",
            "items": {"type": "string"}
        },
        "dependencies": {
            "type": "array",
            "items": {"type": "string"}
        },
        "implementation_details": {
            "type": "array",
            "items": {"type": "string"}
        },
        "potential_issues": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["purpose", "key_functionality", "dependencies", "implementation_details", "potential_issues"]
}

# Schema for requirements
REQUIREMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "pattern": "^RQ-[A-Z_]+-\\d+$"},
        "domain": {"type": "string"},
        "description": {"type": "string"},
        "linked_blocks": {
            "type": "array",
            "items": {"type": "string"}
        },
        "additional_notes": {
            "type": "array",
            "items": {"type": "string"}
        },
        "implementation_files": {
            "type": "array",
            "items": {"type": "string"}
        },
        "implementation_function": {"type": ["string", "null"]}
    },
    "required": ["id", "domain", "description"]
}

# Schema for code references
CODE_REFERENCE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file": {"type": "string"},
        "line": {"type": "integer", "minimum": 1},
        "function": {"type": "string"},
        "type": {"type": "string", "enum": ["implementation", "test"]},
        "url": {"type": "string", "format": "uri"}
    },
    "required": ["file", "line", "type"]
} 