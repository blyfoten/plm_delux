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
- React with TypeScript
- Chakra UI for components
- React Flow for interactive diagrams
- React Hook Form for form management
- React Markdown for content rendering

## Getting Started

### Prerequisites
1. Python 3.12 or higher
2. Node.js 18 or higher
3. Graphviz installed on your system
4. OpenAI API key

### Installation

1. Clone the repository:
bash
git clone https://github.com/yourusername/plm_delux.git
cd plm_delux
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd src/web/frontend
npm install
```

4. Set up environment variables:
```bash
# Windows
set OPENAI_API_KEY=your_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_api_key_here
```

### Running the Application

1. Start the backend server:
```bash
cd src/web
uvicorn backend.api:app --reload
```

2. Start the frontend development server:
```bash
cd src/web/frontend
npm start
```

3. Access the web interface at http://localhost:3000

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

## Usage Examples

### 1. Creating a New Requirement

Using the CLI:
```bash
python src/ai_cli.py generate-requirements -d ui -c "Add support for voice announcements"
```

Using the Web Interface:
1. Navigate to http://localhost:3000
2. Click "Generate Requirement" in the left panel
3. Fill in the domain and context
4. Click "Generate"

### 2. Editing the Architecture

1. Open the web interface
2. Use the visual editor in the right panel
3. Drag blocks to reposition them
4. Connect blocks by dragging between connection points
5. Changes are automatically saved

### 3. Generating Code

1. Select a requirement from the list
2. Click "Generate Code"
3. Review and edit the generated code
4. Save to implement the changes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4 API
- Graphviz for diagram generation
- React Flow for interactive diagrams
- FastAPI for the backend framework
- All other open-source contributors``` 