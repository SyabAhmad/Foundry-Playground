# Foundry Playground

A community-driven API and GUI layer on top of Microsoft Foundry Local, making it easier for developers to use Foundry's local AI models with familiar OpenAI/Claude-style APIs.

## 🚀 Features

- **Simple API Endpoints**: Text generation, embeddings, chat, and more
- **Model Management**: List and interact with any model supported by Foundry Local
- **Custom Training**: Upload your own data for fine-tuning workflows
- **RAG Support**: Build retrieval-augmented generation systems locally
- **Web GUI**: User-friendly interface for model interaction without terminal usage
- **Open Source**: Community-driven development on GitHub

## 📋 Requirements

- Python 3.8+
- Node.js 16+
- Microsoft Foundry Local installed and running

## 🛠️ Installation & Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Microsoft Foundry Local** installed

### 🚀 Quick Start (Windows)

1. **Start Foundry Local:**

```bash
foundry service start
```

You should see: `🟢 Service is already running on http://127.0.0.1:56831/`

2. **Start Foundry Playground:**

```bash
# From the project root directory
start.bat
```

3. **Open your browser:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:5000

### Manual Setup

#### Backend Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

# Initialize the database (creates SQLite tables)
python -c "from app import app, db; app.app_context().push(); db.create_all()"

python app.py
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### ⚙️ Configuration

The app is pre-configured for Foundry Local on `http://127.0.0.1:56831/`. To customize:

Edit `backend/.env`:

```env
FOUNDRY_BASE_URL=http://127.0.0.1:56831
DATABASE_URL=sqlite:///foundry_playground.db
```

## 📖 API Documentation

### Base URL

```
http://localhost:5000/api
```

### Endpoints

#### GET /models

List all available models in Foundry Local.

**Response:**

```json
{
  "success": true,
  "models": [
    {
      "id": "model-1",
      "name": "GPT-2 Small",
      "description": "Small GPT-2 model"
    }
  ],
  "count": 1
}
```

#### POST /generate

Generate text using a Foundry Local model.

**Request:**

```json
{
  "model": "gpt2-small",
  "prompt": "Hello, how are you?",
  "max_tokens": 100,
  "temperature": 0.7
}
```

**Response:**

```json
{
  "success": true,
  "generated_text": "Hello, how are you? I'm doing well, thank you for asking!",
  "model": "gpt2-small",
  "usage": {
    "tokens": 15
  }
}
```

#### POST /embeddings

Generate embeddings for text.

**Request:**

```json
{
  "model": "embedding-model",
  "input": "Your text here"
}
```

#### POST /upload

Upload data files for training or RAG.

**Request:** Form data with `file` field.

**Response:**

```json
{
  "success": true,
  "file_id": "uuid-here",
  "filename": "data.txt",
  "file_path": "/path/to/file"
}
```

#### POST /train

Start a training/fine-tuning job.

**Request:**

```json
{
  "model": "base-model",
  "training_data": "file_id_or_data",
  "type": "fine-tune",
  "parameters": {}
}
```

#### POST /rag

Create a RAG system with uploaded documents.

**Request:**

```json
{
  "documents": ["file_id_1", "file_id_2"],
  "model": "embedding-model",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

## 🔧 Configuration

### Environment Variables

- `FOUNDRY_BASE_URL`: URL where Foundry Local is running (default: http://localhost:8080)
- `FOUNDRY_API_KEY`: API key for Foundry Local authentication (optional)

### Supported File Types for Upload

- Text files (.txt)
- PDFs (.pdf)
- JSON files (.json)
- CSV files (.csv)
- Markdown files (.md)

## 🤝 Contributing

We welcome contributions! This is a community-driven project.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test them
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

**This project is a MenteE initiative and does not belong to Microsoft.** It is an independent, community-driven effort to create developer-friendly tooling around Microsoft's Foundry Local AI runtime. Microsoft is not affiliated with, nor does it endorse, this project.

## 🙏 Acknowledgments

- Microsoft for creating Foundry Local
- The open-source AI community
- All contributors to this project

## 📞 Support

- Create an issue on GitHub
- Join our community discussions
- Check the documentation for common solutions

---

Made with ❤️ by the community
