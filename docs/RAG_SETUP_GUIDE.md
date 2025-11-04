# RAG Corpus Setup Guide

This guide explains how to set up and use the RAG (Retrieval-Augmented Generation) corpus with the Vertex AI service.

## Overview

The RAG corpus allows the AI service to retrieve relevant information from your knowledge base before generating responses. This enables more accurate and contextual answers based on your specific documents and data.

## Prerequisites

1. **Google Cloud Project** with Vertex AI API enabled
2. **GCS Bucket** to store your knowledge base documents
3. **Environment Variables** configured:
   ```bash
   GCP_PROJECT_ID=your-project-id
   GCP_LOCATION=us-central1
   RAG_CORPUS_NAME=your-corpus-name  # Optional: default corpus name
   ```

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your Documents

Upload your knowledge base documents to Google Cloud Storage:

```bash
gsutil cp your-documents/*.pdf gs://your-bucket/knowledge-base/
```

Supported formats:
- PDF
- TXT
- HTML
- Markdown
- DOCX

### 3. Create and Populate the Corpus

Use the setup script to create a corpus and import documents:

```bash
python scripts/setup_rag_corpus.py \
  --corpus-name "my-knowledge-base" \
  --import gs://your-bucket/knowledge-base/*.pdf \
  --chunk-size 512 \
  --chunk-overlap 100
```

**Parameters:**
- `--corpus-name`: Unique name for your corpus
- `--import`: GCS URIs of files to import (supports wildcards)
- `--chunk-size`: Size of text chunks (default: 512 tokens)
- `--chunk-overlap`: Overlap between chunks (default: 100 tokens)

### 4. Test Retrieval

Test if the corpus is working correctly:

```bash
python scripts/setup_rag_corpus.py \
  --corpus-name "my-knowledge-base" \
  --query "What is the refund policy?" \
  --top-k 5
```

## Usage in Code

### Basic Usage

```python
from src.infrastructure.ai.vertex_ai_service import VertexAIService

# Initialize with corpus
service = VertexAIService(corpus_name="my-knowledge-base")

# Generate response with RAG
response = service.generate_response(
    question="What is your refund policy?",
    language="en",
    use_rag=True  # Enable RAG retrieval
)
print(response)
```

### Without RAG (Standard Mode)

```python
# Disable RAG for general questions
response = service.generate_response(
    question="Hello, how are you?",
    language="en",
    use_rag=False  # Disable RAG retrieval
)
```

### Manual Retrieval

```python
# Retrieve contexts without generating response
contexts = service.retrieve_relevant_contexts(
    query="refund policy",
    top_k=5
)

for ctx in contexts:
    print(f"Source: {ctx['source']}")
    print(f"Text: {ctx['text']}")
    print(f"Distance: {ctx['distance']}")
```

### Import Additional Files

```python
# Add more files to existing corpus
service.import_files_to_corpus(
    file_uris=[
        "gs://your-bucket/new-doc1.pdf",
        "gs://your-bucket/new-doc2.pdf"
    ],
    chunk_size=512,
    chunk_overlap=100
)
```

### Get Corpus Information

```python
corpus_info = service.get_corpus_info()
if corpus_info:
    print(f"Corpus: {corpus_info['display_name']}")
    print(f"ID: {corpus_info['name']}")
```

## Integration with Existing App

Update your existing code to use RAG:

```python
# Before (without RAG)
ai_service = VertexAIService()
response = ai_service.generate_response(question, context, language)

# After (with RAG)
ai_service = VertexAIService(corpus_name="my-knowledge-base")
response = ai_service.generate_response(
    question=question,
    context=context,
    language=language,
    use_rag=True  # Enable RAG
)
```

## Best Practices

### 1. Document Preparation
- **Clean your documents**: Remove headers, footers, and irrelevant content
- **Structure matters**: Well-structured documents yield better results
- **File naming**: Use descriptive names for better source tracking

### 2. Chunk Configuration
- **Smaller chunks (256-512)**: Better for precise information retrieval
- **Larger chunks (1024-2048)**: Better for contextual understanding
- **Overlap**: 10-20% of chunk size is recommended

### 3. Query Optimization
- **Specific queries**: More specific questions yield better results
- **Top-K selection**: Start with 3-5, adjust based on results
- **Language consistency**: Match query language with document language

### 4. Performance
- **Cache corpus reference**: Initialize service once, reuse for multiple queries
- **Batch imports**: Import multiple files at once when possible
- **Monitor costs**: RAG queries incur additional API costs

## Troubleshooting

### Corpus Not Found
```
Error: RAG corpus not initialized
```
**Solution**: Ensure `RAG_CORPUS_NAME` is set or pass `corpus_name` to constructor

### Import Fails
```
Error importing files: Permission denied
```
**Solution**: Verify GCS bucket permissions and service account access

### No Results Retrieved
```
Found 0 relevant contexts
```
**Solutions**:
- Check if files were imported successfully
- Verify query matches document content
- Try increasing `top_k` parameter
- Ensure documents are in supported format

### API Errors
```
Error: 403 Vertex AI API not enabled
```
**Solution**: Enable Vertex AI API in Google Cloud Console

## Cost Considerations

RAG operations incur costs for:
1. **Storage**: GCS storage for documents
2. **Indexing**: One-time cost per document
3. **Retrieval**: Per-query cost based on corpus size
4. **Generation**: Standard LLM generation costs

Estimate costs at: https://cloud.google.com/vertex-ai/pricing

## Advanced Configuration

### Custom Chunking Strategy

```python
# For technical documentation
service.import_files_to_corpus(
    file_uris=["gs://bucket/technical-docs/*.pdf"],
    chunk_size=1024,  # Larger chunks for context
    chunk_overlap=200
)

# For FAQs
service.import_files_to_corpus(
    file_uris=["gs://bucket/faqs/*.txt"],
    chunk_size=256,  # Smaller chunks for precision
    chunk_overlap=50
)
```

### Multiple Corpora

```python
# Different corpora for different domains
support_service = VertexAIService(corpus_name="customer-support")
technical_service = VertexAIService(corpus_name="technical-docs")
legal_service = VertexAIService(corpus_name="legal-policies")
```

## Next Steps

1. **Monitor Performance**: Track retrieval quality and adjust parameters
2. **Update Content**: Regularly update corpus with new documents
3. **User Feedback**: Collect feedback to improve retrieval quality
4. **A/B Testing**: Compare RAG vs non-RAG responses

## Support

For issues or questions:
- Check Vertex AI documentation: https://cloud.google.com/vertex-ai/docs
- Review error logs in Cloud Console
- Test with sample queries using the setup script
