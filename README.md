# PLM Delux - Product Lifecycle Management System

A modern PLM-style environment for software requirements management and code analysis, powered by AI.

## Current Features

### 1. Requirements Management
- Store requirements in a machine-readable format
- Group requirements by domain based on source code structure
- AI-assisted requirement generation from code analysis
- Web-based requirement editor and viewer
- Code-to-requirement traceability

### 2. Code Analysis
- Automatic code analysis for requirement mapping
- Function and domain detection
- Caching of analysis results
- Integration with VS Code for source navigation

### 3. AI Integration
- AI-powered requirement generation from code analysis
- Natural language processing of code functions
- Context-aware requirement suggestions

## Quick Start

1. Clone this repository
2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Create a `plm_settings.yaml` file in your workspace:
   ```yaml
   source_folder: "src"  # Root folder for source code
   source_include_patterns:  # Files to analyze
     - "**/*.py"
     - "**/*.cpp"
     - "**/*.hpp"
   ```
4. Start the environment:
   ```bash
   docker compose up --build
   ```
5. Access the services:
   - Frontend: http://localhost:5173
   - VS Code Server: http://localhost:8080
   - Backend API: http://localhost:8000

## Directory Structure

```
plm_delux/
├── work/                  # Mounted workspace directory
│   ├── .plm/            # PLM system cache
│   │   └── analysis_cache/ # Code analysis results
│   ├── requirements/    # Project requirements
│   ├── architecture/   # Architecture definitions
│   └── src/           # Source code
├── src/                  # PLM system source code
│   ├── web/            # Web interface (frontend + backend)
│   └── ai_integration/ # AI integration modules
└── docker-compose.yml    # Container orchestration
```

## Configuration

### PLM Settings
Create a `plm_settings.yaml` file in your workspace with the following options:

```yaml
# Source code configuration
source_folder: "src"  # Root folder for source code
source_include_patterns:  # Files to analyze
  - "**/*.py"   # Python files
  - "**/*.cpp"  # C++ source files
  - "**/*.hpp"  # C++ header files
  - "**/*.h"    # C header files
```

## Using the System

### Mounting Your Project

1. Place your project files in the `work` directory
2. Add your configuration in `work/plm_settings.yaml`
3. The system will automatically create:
   ```
   work/
   ├── .plm/            # System cache directory
   ├── requirements/    # Generated requirements
   └── src/            # Your source code
   ```

### Working with Requirements

1. Access the web interface at http://localhost:5173
2. Click "Analyze Code" to scan your source code
3. Review and edit generated requirements
4. Click on code references to open files in VS Code

### Code Analysis

The system automatically:
1. Analyzes your source code for functions and domains
2. Caches analysis results in `.plm/analysis_cache/`
3. Generates requirements based on code structure
4. Maintains traceability between code and requirements

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

## Planned Features

The following features are planned for future releases:

1. **Architecture Definition**
   - Visual architecture editor
   - Bi-directional requirement linking
   - Automatic diagram generation

2. **Enhanced Visualization**
   - Interactive system diagrams
   - Requirement dependency graphs
   - Block relationship visualization

3. **Git Integration**
   - Branch management from UI
   - Change tracking
   - Version control integration

## License

[License details here]
``` 