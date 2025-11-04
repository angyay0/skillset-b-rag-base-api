#!/usr/bin/env python3
"""
Script to set up and manage RAG corpus for the Vertex AI service.

Usage:
    # Create corpus and import files
    python scripts/setup_rag_corpus.py --corpus-name "my-knowledge-base" --import gs://bucket/docs/*.pdf
    
    # Test retrieval
    python scripts/setup_rag_corpus.py --corpus-name "my-knowledge-base" --query "What is the refund policy?"
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ai.vertex_ai_service import VertexAIService


def main():
    parser = argparse.ArgumentParser(description='Manage RAG corpus for Vertex AI')
    parser.add_argument('--corpus-name', required=True, help='Name of the RAG corpus')
    parser.add_argument('--import', dest='import_files', nargs='+', 
                       help='GCS URIs to import (e.g., gs://bucket/file.pdf)')
    parser.add_argument('--query', help='Test query to retrieve relevant contexts')
    parser.add_argument('--chunk-size', type=int, default=512, 
                       help='Chunk size for document splitting (default: 512)')
    parser.add_argument('--chunk-overlap', type=int, default=100,
                       help='Overlap between chunks (default: 100)')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of top results to retrieve (default: 5)')
    
    args = parser.parse_args()
    
    # Initialize service with corpus
    print(f"Initializing Vertex AI service with corpus: {args.corpus_name}")
    service = VertexAIService(corpus_name=args.corpus_name)
    
    # Display corpus info
    corpus_info = service.get_corpus_info()
    if corpus_info:
        print(f"\nCorpus Information:")
        print(f"  Name: {corpus_info['name']}")
        print(f"  Display Name: {corpus_info['display_name']}")
        print(f"  Description: {corpus_info['description']}")
    
    # Import files if provided
    if args.import_files:
        print(f"\nImporting {len(args.import_files)} files to corpus...")
        try:
            service.import_files_to_corpus(
                file_uris=args.import_files,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )
            print("✓ Files imported successfully")
        except Exception as e:
            print(f"✗ Error importing files: {str(e)}")
            return 1
    
    # Test query if provided
    if args.query:
        print(f"\nTesting retrieval with query: '{args.query}'")
        contexts = service.retrieve_relevant_contexts(args.query, top_k=args.top_k)
        
        if contexts:
            print(f"\nFound {len(contexts)} relevant contexts:")
            for idx, ctx in enumerate(contexts, 1):
                print(f"\n--- Context {idx} ---")
                print(f"Source: {ctx['source']}")
                if ctx['distance']:
                    print(f"Distance: {ctx['distance']:.4f}")
                print(f"Text: {ctx['text'][:200]}..." if len(ctx['text']) > 200 else f"Text: {ctx['text']}")
        else:
            print("No relevant contexts found")
    
    print("\n✓ Done!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
