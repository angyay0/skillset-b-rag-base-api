#!/usr/bin/env python3
"""
Unit tests for RAG-enhanced Vertex AI service.

Run with: python -m pytest tests/test_rag_service.py -v
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ai.vertex_ai_service import VertexAIService


class TestVertexAIServiceRAG:
    """Test suite for RAG functionality"""
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project', 'GCP_LOCATION': 'us-central1'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    def test_init_without_corpus(self, mock_model, mock_init):
        """Test initialization without RAG corpus"""
        service = VertexAIService()
        
        assert service.project_id == 'test-project'
        assert service.location == 'us-central1'
        assert service.corpus_name is None
        assert service.rag_corpus is None
        mock_init.assert_called_once_with(project='test-project', location='us-central1')
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project', 'RAG_CORPUS_NAME': 'test-corpus'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.list_corpora')
    def test_init_with_corpus_from_env(self, mock_list_corpora, mock_model, mock_init):
        """Test initialization with corpus from environment variable"""
        mock_corpus = Mock()
        mock_corpus.display_name = 'test-corpus'
        mock_corpus.name = 'projects/test/corpora/123'
        mock_list_corpora.return_value = [mock_corpus]
        
        service = VertexAIService()
        
        assert service.corpus_name == 'test-corpus'
        assert service.rag_corpus is not None
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.list_corpora')
    def test_init_with_explicit_corpus(self, mock_list_corpora, mock_model, mock_init):
        """Test initialization with explicit corpus name"""
        mock_corpus = Mock()
        mock_corpus.display_name = 'my-corpus'
        mock_corpus.name = 'projects/test/corpora/456'
        mock_list_corpora.return_value = [mock_corpus]
        
        service = VertexAIService(corpus_name='my-corpus')
        
        assert service.corpus_name == 'my-corpus'
        assert service.rag_corpus is not None
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.list_corpora')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.create_corpus')
    def test_create_new_corpus(self, mock_create_corpus, mock_list_corpora, mock_model, mock_init):
        """Test creating a new corpus when it doesn't exist"""
        mock_list_corpora.return_value = []
        mock_new_corpus = Mock()
        mock_new_corpus.display_name = 'new-corpus'
        mock_new_corpus.name = 'projects/test/corpora/789'
        mock_create_corpus.return_value = mock_new_corpus
        
        service = VertexAIService(corpus_name='new-corpus')
        
        assert service.rag_corpus is not None
        mock_create_corpus.assert_called_once()
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    def test_generate_response_without_rag(self, mock_model_class, mock_init):
        """Test generating response without RAG"""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Hello! How can I help you?"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        service = VertexAIService()
        response = service.generate_response(
            question="Hello",
            language="en",
            use_rag=False
        )
        
        assert response == "Hello! How can I help you?"
        mock_model.generate_content.assert_called_once()
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.list_corpora')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.retrieval_query')
    def test_generate_response_with_rag(self, mock_retrieval, mock_list_corpora, 
                                       mock_model_class, mock_init):
        """Test generating response with RAG"""
        # Setup corpus
        mock_corpus = Mock()
        mock_corpus.display_name = 'test-corpus'
        mock_corpus.name = 'projects/test/corpora/123'
        mock_list_corpora.return_value = [mock_corpus]
        
        # Setup retrieval response
        mock_context = Mock()
        mock_context.text = "Our refund policy allows returns within 30 days."
        mock_context.source_uri = "gs://bucket/policy.pdf"
        mock_context.distance = 0.85
        
        mock_retrieval_response = Mock()
        mock_retrieval_response.contexts.contexts = [mock_context]
        mock_retrieval.return_value = mock_retrieval_response
        
        # Setup model response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "According to our policy, you can return items within 30 days."
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        service = VertexAIService(corpus_name='test-corpus')
        response = service.generate_response(
            question="What is your refund policy?",
            language="en",
            use_rag=True
        )
        
        assert "30 days" in response
        mock_retrieval.assert_called_once()
        mock_model.generate_content.assert_called_once()
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.list_corpora')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.retrieval_query')
    def test_retrieve_relevant_contexts(self, mock_retrieval, mock_list_corpora, 
                                        mock_model, mock_init):
        """Test retrieving relevant contexts"""
        # Setup corpus
        mock_corpus = Mock()
        mock_corpus.display_name = 'test-corpus'
        mock_corpus.name = 'projects/test/corpora/123'
        mock_list_corpora.return_value = [mock_corpus]
        
        # Setup retrieval response
        mock_context1 = Mock()
        mock_context1.text = "Context 1"
        mock_context1.source_uri = "gs://bucket/doc1.pdf"
        mock_context1.distance = 0.9
        
        mock_context2 = Mock()
        mock_context2.text = "Context 2"
        mock_context2.source_uri = "gs://bucket/doc2.pdf"
        mock_context2.distance = 0.8
        
        mock_retrieval_response = Mock()
        mock_retrieval_response.contexts.contexts = [mock_context1, mock_context2]
        mock_retrieval.return_value = mock_retrieval_response
        
        service = VertexAIService(corpus_name='test-corpus')
        contexts = service.retrieve_relevant_contexts("test query", top_k=2)
        
        assert len(contexts) == 2
        assert contexts[0]['text'] == "Context 1"
        assert contexts[0]['source'] == "gs://bucket/doc1.pdf"
        assert contexts[0]['distance'] == 0.9
        assert contexts[1]['text'] == "Context 2"
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.list_corpora')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.import_files')
    def test_import_files_to_corpus(self, mock_import, mock_list_corpora, 
                                    mock_model, mock_init):
        """Test importing files to corpus"""
        # Setup corpus
        mock_corpus = Mock()
        mock_corpus.display_name = 'test-corpus'
        mock_corpus.name = 'projects/test/corpora/123'
        mock_list_corpora.return_value = [mock_corpus]
        
        service = VertexAIService(corpus_name='test-corpus')
        file_uris = ["gs://bucket/doc1.pdf", "gs://bucket/doc2.pdf"]
        
        service.import_files_to_corpus(file_uris, chunk_size=512, chunk_overlap=100)
        
        mock_import.assert_called_once_with(
            corpus_name='projects/test/corpora/123',
            paths=file_uris,
            chunk_size=512,
            chunk_overlap=100
        )
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    @patch('src.infrastructure.ai.vertex_ai_service.rag.list_corpora')
    def test_get_corpus_info(self, mock_list_corpora, mock_model, mock_init):
        """Test getting corpus information"""
        # Setup corpus
        mock_corpus = Mock()
        mock_corpus.display_name = 'test-corpus'
        mock_corpus.name = 'projects/test/corpora/123'
        mock_corpus.description = 'Test corpus description'
        mock_list_corpora.return_value = [mock_corpus]
        
        service = VertexAIService(corpus_name='test-corpus')
        info = service.get_corpus_info()
        
        assert info is not None
        assert info['name'] == 'projects/test/corpora/123'
        assert info['display_name'] == 'test-corpus'
        assert info['description'] == 'Test corpus description'
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    def test_get_corpus_info_no_corpus(self, mock_model, mock_init):
        """Test getting corpus info when no corpus is initialized"""
        service = VertexAIService()
        info = service.get_corpus_info()
        
        assert info is None
    
    @patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'})
    @patch('src.infrastructure.ai.vertex_ai_service.vertexai.init')
    @patch('src.infrastructure.ai.vertex_ai_service.GenerativeModel')
    def test_multilingual_support(self, mock_model_class, mock_init):
        """Test multilingual response generation"""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        languages = ['es', 'en', 'pt']
        service = VertexAIService()
        
        for lang in languages:
            mock_response = Mock()
            mock_response.text = f"Response in {lang}"
            mock_model.generate_content.return_value = mock_response
            
            response = service.generate_response(
                question="Test question",
                language=lang,
                use_rag=False
            )
            
            assert response == f"Response in {lang}"


if __name__ == '__main__':
    print("Run tests with: python -m pytest tests/test_rag_service.py -v")
