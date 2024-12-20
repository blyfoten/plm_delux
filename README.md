# PLM Delux - Product Lifecycle Management System

A modern PLM-style environment for software requirements, architecture definition, and code generation, powered by AI.

## Quick Start

1. Clone this repository
2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Start the environment:
   ```bash
   docker compose up
   ```
4. Access the services:
   - Frontend: http://localhost:5173
   - VS Code Server: http://localhost:8080
   - Backend API: http://localhost:8000

## Directory Structure

```
plm_delux/
├── work/                  # Mounted workspace directory
│   ├── requirements/     # Project requirements
│   ├── architecture/    # Architecture definitions
│   └── generated/      # Generated code
├── src/                  # PLM system source code
│   ├── web/            # Web interface (frontend + backend)
│   ├── ai_integration/ # AI integration modules
│   └── prompts/       # AI prompt templates
└── docker-compose.yml    # Container orchestration
```

## Using the System

### Mounting Your Project

1. Place your project files in the `work` directory
2. The directory structure should be:
   ```
   work/
   ├── requirements/     # Your project requirements
   ├── architecture/    # Your architecture definitions
   └── generated/      # Generated code will be placed here
   ```

### Working with Requirements

1. Access the web interface at http://localhost:5173
2. Use the UI to create and manage requirements
3. Requirements are stored as markdown files in `work/requirements/`

### Editing Code

1. Access VS Code Server at http://localhost:8080
2. The entire `/work` directory is available as your workspace
3. Click on code links in the requirements UI to open the corresponding files

### Git Integration

The system supports Git operations on your mounted repository:
1. Create new branches from the UI
2. Switch between branches
3. All Git operations are performed on your actual repository in `/work`

## Development

### Building from Source

```bash
# Build all containers
docker compose build

# Start the environment
docker compose up
```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required for AI features)
- `WORKSPACE_DIR`: Directory for project files (default: /work)

## License

[License details here]
``` 