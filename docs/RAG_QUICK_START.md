# RAG Quick Start Guide

Get started with RAG (Retrieval-Augmented Generation) in 5 minutes.

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_LOCATION="us-central1"
export RAG_CORPUS_NAME="my-knowledge-base"  # Optional
```

### 3. Upload Documents to GCS
```bash
# Upload your knowledge base documents
gsutil cp docs/*.pdf gs://your-bucket/knowledge-base/
```

### 4. Create Corpus and Import Documents
```bash
python scripts/setup_rag_corpus.py \
  --corpus-name "my-knowledge-base" \
  --import gs://your-bucket/knowledge-base/*.pdf
```

### 5. Test It!
```python
from src.infrastructure.ai.vertex_ai_service import VertexAIService

# Initialize with RAG
service = VertexAIService(corpus_name="my-knowledge-base")

# Ask a question
response = service.generate_response(
    question="What is your refund policy?",
    language="en",
    use_rag=True
)

print(response)
```

## Key Features

### ✅ Automatic Corpus Management
- Creates corpus if it doesn't exist
- Reuses existing corpus automatically

### ✅ Document Import
```python
service.import_files_to_corpus(
    file_uris=["gs://bucket/doc1.pdf", "gs://bucket/doc2.pdf"],
    chunk_size=512,
    chunk_overlap=100
)
```

### ✅ Context Retrieval
```python
contexts = service.retrieve_relevant_contexts(
    query="refund policy",
    top_k=5
)
```

### ✅ RAG-Enhanced Generation
```python
# With RAG (uses knowledge base)
response = service.generate_response(
    question="What are your hours?",
    use_rag=True
)

# Without RAG (general knowledge only)
response = service.generate_response(
    question="Hello!",
    use_rag=False
)
```

## Common Use Cases

### Customer Support
```python
service = VertexAIService(corpus_name="support-docs")
response = service.generate_response(
    question="How do I reset my password?",
    language="en",
    use_rag=True
)
```

### Product Information
```python
service = VertexAIService(corpus_name="product-catalog")
response = service.generate_response(
    question="What are the specs of Model X?",
    language="en",
    use_rag=True
)
```

### Policy Questions
```python
service = VertexAIService(corpus_name="company-policies")
response = service.generate_response(
    question="What is the vacation policy?",
    language="en",
    use_rag=True
)
```

## Testing

Run the example script:
```bash
python examples/rag_example.py
```

Test retrieval:
```bash
python scripts/setup_rag_corpus.py \
  --corpus-name "my-knowledge-base" \
  --query "your test query"
```

## Troubleshooting

### "RAG corpus not initialized"
➜ Set `RAG_CORPUS_NAME` environment variable or pass `corpus_name` to constructor

### "No relevant contexts found"
➜ Check if documents were imported successfully
➜ Try a more specific query
➜ Increase `top_k` parameter

### "Permission denied"
➜ Verify GCP credentials: `gcloud auth application-default login`
➜ Check service account has Vertex AI permissions

## Next Steps

📖 Read the [full setup guide](./RAG_SETUP_GUIDE.md) for advanced configuration

🔧 Customize chunk size and overlap for your use case

📊 Monitor retrieval quality and adjust parameters

💡 Experiment with different corpus configurations

## Support

- [Vertex AI RAG Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/rag-api)
- [Setup Guide](./RAG_SETUP_GUIDE.md)
- [Example Code](../examples/rag_example.py)
