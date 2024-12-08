# PLM Delux - Product Lifecycle Management System

A modern PLM-style environment for software requirements, architecture definition, and code generation, powered by AI.

## Features

### 1. Requirements Management
- Store requirements in a machine-readable, lightweight format (Markdown with YAML front matter)
- Group requirements by domain (UI, Motor Control, etc.)
- AI-assisted requirement generation
- Web-based requirement editor and viewer
- Real-time updates and collaboration

### 2. Architecture Definition
- Visual architecture editor with drag-and-drop interface
- Bi-directional linking between requirements and architecture blocks
- Automatic diagram generation using Graphviz
- AI-powered architecture improvement suggestions
- Version control and change tracking

### 3. Code Generation
- AI-assisted code generation from requirements
- Automatic test case generation
- Code stub creation with proper documentation
- Type-safe implementations with modern best practices
- Integration with existing codebases

### 4. Visualization
- Interactive system architecture diagrams
- Requirement dependency graphs
- Block relationship visualization
- Real-time updates as architecture changes

## Tech Stack

### Backend
- Python 3.12+
- FastAPI for REST API
- OpenAI GPT-4 for AI capabilities
- Graphviz for diagram generation
- YAML and Markdown for requirement storage

### Frontend
- React 18 with TypeScript
- Chakra UI for components
- React Flow for interactive diagrams
- React Hook Form for form management
- React Markdown for content rendering

## Getting Started

### Prerequisites

1. Python 3.12 or higher
2. Node.js 18 or higher
3. Graphviz (for diagram generation)
4. OpenAI API key

#### Installing Graphviz

- **Windows**: 
  1. Download from [Graphviz Download Page](https://graphviz.org/download/)
  2. Add the bin directory to your PATH
  3. Verify installation: `dot -V`

- **macOS**:
  ```bash
  brew install graphviz
  ```

- **Linux**:
  ```bash
  sudo apt-get install graphviz  # Ubuntu/Debian
  sudo dnf install graphviz      # Fedora
  ```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/plm_delux.git
cd plm_delux
```

2. Create and activate a Python virtual environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Windows
set OPENAI_API_KEY=your_api_key_here

# Linux/macOS
export OPENAI_API_KEY=your_api_key_here
```

5. Install frontend dependencies:
```bash
cd src/web/frontend
npm install --legacy-peer-deps
```

### Running the Application

1. Start the backend server:
```bash
cd src/web
uvicorn backend.api:app --reload
```
The backend will be available at http://localhost:8000

2. Start the frontend development server (in a new terminal):
```bash
cd src/web/frontend
npm run dev
```
The frontend will be available at http://localhost:5173

## Development Workflow

### Adding New Requirements

1. Using the Web Interface:
   - Navigate to http://localhost:5173
   - Click "Generate Requirement" in the left panel
   - Fill in the domain and context
   - Click "Generate"

2. Using the CLI:
   ```bash
   python src/ai_cli.py generate-requirements -d ui -c "Add support for voice announcements"
   ```

### Editing the Architecture

1. Open the web interface
2. Use the visual editor in the right panel:
   - Drag blocks to reposition them
   - Connect blocks by dragging between connection points
   - Edit block properties by clicking on them
   - Changes are automatically saved

### Generating Code

1. Select a requirement from the list
2. Click "Generate Code"
3. Review and edit the generated code
4. Save to implement the changes

## Project Structure

```
plm_delux/
├── requirements/           # Requirement markdown files
│   ├── ui/               # UI domain requirements
│   ├── motor_and_doors/  # Motor control requirements
│   └── offboard/        # External connectivity requirements
├── src/
│   ├── ai_integration/   # AI integration modules
│   ├── architecture/     # Architecture definition
│   ├── code_generator/   # Code generation logic
│   ├── visualizer/       # Visualization tools
│   └── web/             # Web interface
│       ├── backend/     # FastAPI backend
│       └── frontend/    # React frontend
├── docs/                 # Generated documentation
└── tests/               # Test suites
```

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   ```
   ModuleNotFoundError: No module named 'ai_integration'
   ```
   Solutions:
   - The error occurs because Python can't find the modules in the src directory. Fix it by:
     
     a. Setting PYTHONPATH (recommended for development):
     ```bash
     # Windows
     set PYTHONPATH=%PYTHONPATH%;C:\path\to\plm_delux\src

     # Linux/macOS
     export PYTHONPATH=$PYTHONPATH:/path/to/plm_delux/src
     ```
     
     b. Installing the package in development mode:
     ```bash
     pip install -e .
     ```
     
     c. The backend API already includes code to add src to Python path, but you might need this for other scripts.

2. **Graphviz Not Found**
   ```
   graphviz.backend.execute.ExecutableNotFound: failed to execute ['dot']
   ```
   Solution: Install Graphviz and ensure it's in your PATH
   - Windows: Restart your terminal after installing Graphviz
   - Check installation: `dot -V`

3. **Frontend Dependencies Conflict**
   ```
   npm ERR! ERESOLVE unable to resolve dependency tree
   ```
   Solution: Use `npm install --legacy-peer-deps`

4. **OpenAI API Key Not Found**
   ```
   ValueError: OpenAI API key must be provided
   ```
   Solution: Set the OPENAI_API_KEY environment variable

5. **Backend Connection Failed**
   ```
   Failed to fetch: http://localhost:8000/api/...
   ```
   Solution: Ensure the backend server is running and CORS is properly configured

### Development Tips

1. **Hot Reload**
   - Backend: The `--reload` flag with uvicorn enables auto-reload
   - Frontend: Vite provides fast hot module replacement (HMR)

2. **API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Debugging**
   - Backend: Use `logging.debug()` statements
   - Frontend: Use React DevTools and Network tab

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Guidelines

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Use meaningful commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4 API
- Graphviz for diagram generation
- React Flow for interactive diagrams
- FastAPI for the backend framework
- All other open-source contributors
``` 