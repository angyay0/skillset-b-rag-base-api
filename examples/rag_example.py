#!/usr/bin/env python3
"""
Example demonstrating RAG corpus usage with Vertex AI service.

This example shows:
1. Initializing the service with a RAG corpus
2. Retrieving relevant contexts
3. Generating responses with RAG-enhanced context
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ai.vertex_ai_service import VertexAIService


def example_with_rag():
    """Example using RAG corpus for enhanced responses"""
    print("=" * 60)
    print("Example 1: Using RAG Corpus")
    print("=" * 60)
    
    # Initialize service with corpus
    # The corpus should already exist and have documents imported
    corpus_name = os.getenv('RAG_CORPUS_NAME', 'my-knowledge-base')
    service = VertexAIService(corpus_name=corpus_name)
    
    # Check corpus info
    corpus_info = service.get_corpus_info()
    if corpus_info:
        print(f"\n✓ Connected to corpus: {corpus_info['display_name']}")
    else:
        print("\n⚠ No corpus configured. Responses will be generated without RAG.")
    
    # Example question
    question = "What is your refund policy?"
    print(f"\nQuestion: {question}")
    
    # Retrieve relevant contexts first (optional - for demonstration)
    print("\n--- Retrieving Relevant Contexts ---")
    contexts = service.retrieve_relevant_contexts(question, top_k=3)
    
    if contexts:
        print(f"Found {len(contexts)} relevant contexts:")
        for idx, ctx in enumerate(contexts, 1):
            print(f"\n[{idx}] Source: {ctx['source']}")
            print(f"    Text preview: {ctx['text'][:150]}...")
    else:
        print("No relevant contexts found in corpus")
    
    # Generate response with RAG
    print("\n--- Generating Response with RAG ---")
    response = service.generate_response(
        question=question,
        language="en",
        use_rag=True  # Enable RAG
    )
    print(f"\nResponse:\n{response}")


def example_without_rag():
    """Example without using RAG corpus"""
    print("\n" + "=" * 60)
    print("Example 2: Without RAG Corpus (Standard Mode)")
    print("=" * 60)
    
    # Initialize service without corpus
    service = VertexAIService()
    
    # General question that doesn't need specific knowledge
    question = "Hello! Can you help me?"
    print(f"\nQuestion: {question}")
    
    # Generate response without RAG
    print("\n--- Generating Response (No RAG) ---")
    response = service.generate_response(
        question=question,
        language="en",
        use_rag=False  # Disable RAG
    )
    print(f"\nResponse:\n{response}")


def example_comparison():
    """Compare responses with and without RAG"""
    print("\n" + "=" * 60)
    print("Example 3: Comparison - With vs Without RAG")
    print("=" * 60)
    
    corpus_name = os.getenv('RAG_CORPUS_NAME', 'my-knowledge-base')
    service = VertexAIService(corpus_name=corpus_name)
    
    question = "What are your business hours?"
    print(f"\nQuestion: {question}")
    
    # Response WITH RAG
    print("\n--- Response WITH RAG ---")
    response_with_rag = service.generate_response(
        question=question,
        language="en",
        use_rag=True
    )
    print(response_with_rag)
    
    # Response WITHOUT RAG
    print("\n--- Response WITHOUT RAG ---")
    response_without_rag = service.generate_response(
        question=question,
        language="en",
        use_rag=False
    )
    print(response_without_rag)
    
    print("\n" + "=" * 60)
    print("Notice how the RAG-enhanced response uses specific")
    print("information from your knowledge base, while the standard")
    print("response provides a more general answer.")
    print("=" * 60)


def example_multilingual():
    """Example with multiple languages"""
    print("\n" + "=" * 60)
    print("Example 4: Multilingual RAG Support")
    print("=" * 60)
    
    corpus_name = os.getenv('RAG_CORPUS_NAME', 'my-knowledge-base')
    service = VertexAIService(corpus_name=corpus_name)
    
    questions = {
        'en': "What is your return policy?",
        'es': "¿Cuál es su política de devoluciones?",
        'pt': "Qual é a sua política de devolução?"
    }
    
    for lang, question in questions.items():
        print(f"\n--- Language: {lang.upper()} ---")
        print(f"Question: {question}")
        
        response = service.generate_response(
            question=question,
            language=lang,
            use_rag=True
        )
        print(f"Response: {response[:200]}...")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("RAG Corpus Examples for Vertex AI Service")
    print("=" * 60)
    
    try:
        # Run examples
        example_with_rag()
        example_without_rag()
        
        # Optional: Run comparison and multilingual examples
        # Uncomment if you want to see these
        # example_comparison()
        # example_multilingual()
        
        print("\n" + "=" * 60)
        print("✓ Examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {str(e)}")
        print("\nMake sure:")
        print("1. GCP_PROJECT_ID is set in your environment")
        print("2. You have proper GCP credentials configured")
        print("3. Vertex AI API is enabled in your project")
        print("4. RAG corpus exists (if using RAG examples)")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
