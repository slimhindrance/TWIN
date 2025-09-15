# Digital Twin 🧠

A conversational AI application that creates your personal digital twin by ingesting and learning from your Obsidian vault. Built with FastAPI, React, and OpenAI, this scalable system provides intelligent access to your personal knowledge base with near-perfect memory.

## ✨ Features

- **🤖 Conversational AI**: Chat with a version of yourself that has access to all your notes
- **📚 Knowledge Base**: Automatic ingestion and indexing of Obsidian markdown files  
- **🔄 Real-time Sync**: File watching and automatic synchronization with your vault
- **🔍 Smart Search**: Semantic search through your personal knowledge base
- **📝 Source Attribution**: Every response includes citations from your notes
- **🎨 Modern UI**: Beautiful, responsive React interface with Tailwind CSS
- **🐳 Cloud Ready**: Docker configuration for easy deployment anywhere
- **⚡ Scalable**: Built with FastAPI for high performance and extensibility

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  Obsidian Vault │
│   (TypeScript)   │◄──►│     (Python)     │◄──►│   (Markdown)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Modern Web UI  │    │   ChromaDB      │    │  File Watcher   │
│   - Chat        │    │ Vector Store    │    │   (Watchdog)    │
│   - Search      │    └─────────────────┘    └─────────────────┘
│   - Settings    │              │                       
└─────────────────┘              ▼                       
                        ┌─────────────────┐              
                        │   OpenAI API    │              
                        │  - GPT-4        │              
                        │  - Embeddings   │              
                        └─────────────────┘              
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- Obsidian vault

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/digital-twin.git
   cd digital-twin
   ```

2. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   ```
   Edit `backend/.env` and add your OpenAI API key and vault path.

3. **Build and run**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Open http://localhost:8000 in your browser
   - The API docs are available at http://localhost:8000/docs

### Option 2: Local Development

1. **Backend Setup**
   ```bash
   cd backend
   pip install poetry
   poetry install
   cp .env.example .env
   # Edit .env file with your configuration
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

3. **Run the application**
   ```bash
   # Terminal 1: Backend
   cd backend
   poetry run uvicorn app.main:app --reload

   # Terminal 2: Frontend  
   cd frontend
   npm start
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend` directory with the following:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# Optional (with defaults)
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
CHROMA_PERSIST_DIRECTORY=./chroma_db
COLLECTION_NAME=digital_twin_knowledge
BACKEND_CORS_ORIGINS=http://localhost:3000
```

### Obsidian Vault Setup

1. **Point to your vault**: Set `OBSIDIAN_VAULT_PATH` to your Obsidian vault directory
2. **Initial sync**: Use the Settings panel to trigger a full synchronization
3. **Auto-sync**: Enable file watching to automatically sync changes

## 💬 Usage

### Starting a Conversation

1. Open the application in your browser
2. Start chatting with your digital twin
3. Ask about anything in your notes:
   - "What did I learn about machine learning last month?"
   - "Summarize my thoughts on productivity systems"
   - "What were the key insights from my project retrospective?"

### Searching Your Knowledge

1. Click the search icon in the chat interface
2. Enter your query using natural language
3. Browse results with similarity scores
4. Click results to see more details

### Managing Your Vault

1. Click the settings icon to open configuration
2. Set your vault path
3. Monitor sync status and health
4. Trigger manual synchronization when needed

## 🛠️ API Documentation

The FastAPI backend provides a comprehensive REST API:

- **Chat**: `/api/v1/chat` - Conversational AI endpoints
- **Search**: `/api/v1/search` - Knowledge base search
- **Sync**: `/api/v1/sync` - Vault synchronization management  
- **Health**: `/api/v1/health` - System health monitoring

Visit http://localhost:8000/docs for interactive API documentation.

## 🔧 Development

### Project Structure

```
digital-twin/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   ├── core/           # Configuration
│   │   ├── models/         # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── pyproject.toml      # Poetry configuration
│   └── .env.example
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   └── App.tsx
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml      # Production deployment
├── docker-compose.dev.yml  # Development environment
└── README.md
```

### Adding New Features

1. **Backend**: Add routes in `backend/app/api/v1/`
2. **Frontend**: Create components in `frontend/src/components/`
3. **Services**: Add business logic in `backend/app/services/`
4. **Models**: Define schemas in `backend/app/models/schemas.py`

### Running Tests

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

The project uses modern development practices:

- **Backend**: Black, isort, flake8, mypy for Python code quality
- **Frontend**: ESLint, Prettier for TypeScript/React code quality
- **Pre-commit hooks**: Automatic formatting and linting

## 🚀 Deployment

### Cloud Deployment

The application is designed for easy cloud deployment:

1. **Docker Hub**
   ```bash
   docker build -t yourusername/digital-twin .
   docker push yourusername/digital-twin
   ```

2. **Cloud Platforms**
   - AWS ECS/Fargate
   - Google Cloud Run
   - Azure Container Instances
   - Railway, Render, or similar PaaS

3. **Kubernetes**
   ```bash
   kubectl apply -f k8s/
   ```

### Environment-Specific Configurations

- **Development**: Uses `docker-compose.dev.yml` with hot reload
- **Production**: Uses `docker-compose.yml` with optimized builds
- **Environment variables**: Customize behavior per environment

## 🔒 Security Considerations

- **API Keys**: Never commit API keys to version control
- **CORS**: Configure allowed origins in production
- **Authentication**: Consider adding user authentication for multi-user deployments
- **Rate Limiting**: Built-in rate limiting protects against abuse
- **Data Privacy**: Your notes never leave your infrastructure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Add tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

1. **"OpenAI API key not provided"**
   - Check your `.env` file in the backend directory
   - Ensure `OPENAI_API_KEY` is set correctly

2. **"Invalid vault path"**  
   - Verify the path exists and contains `.md` files
   - Check file permissions
   - Ensure the path is absolute

3. **Frontend can't connect to backend**
   - Verify backend is running on port 8000
   - Check CORS configuration
   - Ensure `REACT_APP_API_URL` is correct

4. **Docker build fails**
   - Ensure Docker has enough memory allocated
   - Check for port conflicts
   - Verify all files are present

### Performance Tips

- **Large vaults**: Consider chunking strategy for very large note collections
- **Memory usage**: Monitor ChromaDB memory usage with large datasets
- **API limits**: Be aware of OpenAI API rate limits and costs

### Getting Help

- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review logs in the Docker containers
- Join our community discussions

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python framework
- [React](https://reactjs.org/) for the frontend framework
- [OpenAI](https://openai.com/) for the AI capabilities
- [ChromaDB](https://www.trychroma.com/) for vector database
- [Obsidian](https://obsidian.md/) for the inspiration and note-taking system

---

**Built with ❤️ for knowledge workers who want perfect memory**

*Remember: With great memory comes great responsibility. Use your digital twin wisely!*
