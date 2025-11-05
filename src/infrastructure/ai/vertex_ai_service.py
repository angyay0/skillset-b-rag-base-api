import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel
try:
    from vertexai.preview import rag
except ImportError:
    # RAG not available in this version
    rag = None
from typing import List, Dict, Optional


class VertexAIService:
    """Vertex AI service for generating responses with RAG capabilities"""
    
    def __init__(self, corpus_name: Optional[str] = None):
        project_id = os.getenv('GCP_PROJECT_ID')
        location = os.getenv('GCP_LOCATION', 'us-central1')
        
        if not project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        self.project_id = project_id
        self.location = location
        self.corpus_name = corpus_name or os.getenv('RAG_CORPUS_NAME')
        self.rag_corpus = None
        
        # Try to initialize Vertex AI
        try:
            vertexai.init(project=project_id, location=location)
            self.model = GenerativeModel("gemini-2.5-flash")
            
            # Initialize RAG corpus if name is provided
            if self.corpus_name:
                try:
                    self.rag_corpus = self._get_or_create_corpus(self.corpus_name)
                except Exception as e:
                    print(f"Warning: Could not initialize RAG corpus: {str(e)}")
        except Exception as e:
            print(f"Error initializing Vertex AI: {str(e)}")
            print("Application will continue without AI capabilities")
            self.model = None
    
    def _get_or_create_corpus(self, corpus_display_name: str):
        """Get existing corpus or create a new one"""
        if rag is None:
            print("Warning: RAG module not available in this version of google-cloud-aiplatform")
            return None
        
        try:
            # List existing corpora
            corpora = rag.list_corpora()
            for corpus in corpora:
                if corpus.display_name == corpus_display_name:
                    print(f"Found existing corpus: {corpus.name}")
                    return corpus
            
            # Create new corpus if not found
            print(f"Creating new RAG corpus: {corpus_display_name}")
            corpus = rag.create_corpus(
                display_name=corpus_display_name,
                description=f"RAG corpus for {corpus_display_name}"
            )
            return corpus
        except Exception as e:
            print(f"Error managing corpus: {str(e)}")
            return None
    
    def import_files_to_corpus(self, file_uris: List[str], chunk_size: int = 512, chunk_overlap: int = 100):
        """Import files into the RAG corpus
        
        Args:
            file_uris: List of GCS URIs (gs://bucket/path/to/file)
            chunk_size: Size of text chunks for indexing
            chunk_overlap: Overlap between chunks
        """
        if rag is None:
            raise ValueError("RAG module not available in this version of google-cloud-aiplatform")
        
        if not self.rag_corpus:
            raise ValueError("RAG corpus not initialized. Provide corpus_name during initialization.")
        
        try:
            print(f"Importing {len(file_uris)} files to corpus...")
            rag.import_files(
                corpus_name=self.rag_corpus.name,
                paths=file_uris,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            print("Files imported successfully")
        except Exception as e:
            print(f"Error importing files: {str(e)}")
            raise
    
    def retrieve_relevant_contexts(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant contexts from the RAG corpus
        
        Args:
            query: The search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant context chunks with metadata
        """
        if rag is None or not self.rag_corpus:
            return []
        
        try:
            # Retrieve relevant contexts
            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=self.rag_corpus.name,
                    )
                ],
                text=query,
                similarity_top_k=top_k
            )
            
            contexts = []
            for context in response.contexts.contexts:
                contexts.append({
                    'text': context.text,
                    'source': context.source_uri if hasattr(context, 'source_uri') else 'unknown',
                    'distance': context.distance if hasattr(context, 'distance') else None
                })
            
            return contexts
        except Exception as e:
            print(f"Error retrieving contexts: {str(e)}")
            return []
    
    def generate_response(self, question: str, context: str = None, language: str = 'es', use_rag: bool = True, max_output_tokens: int = 110) -> str:
        """Generate response from Vertex AI model with optional RAG retrieval
        
        Args:
            question: User's question
            context: Conversation context
            language: Response language (es, en, pt)
            use_rag: Whether to use RAG retrieval for additional context
            max_output_tokens: Maximum number of tokens in response (default: 300, ~225 words)
                             - 150 tokens ≈ 110 words (very concise)
                             - 300 tokens ≈ 225 words (concise, recommended for chat)
                             - 500 tokens ≈ 375 words (moderate)
                             - 1000 tokens ≈ 750 words (detailed)
        """
        # Check if model is initialized
        if self.model is None:
            error_messages = {
                'es': 'Lo siento, el servicio de IA no está disponible en este momento. Por favor, contacta al administrador.',
                'en': 'Sorry, the AI service is not available at the moment. Please contact the administrator.',
                'pt': 'Desculpe, o serviço de IA não está disponível no momento. Entre em contato com o administrador.'
            }
            return error_messages.get(language, error_messages['es'])
        
        try:
            # Build prompt based on language with Blinky's personality
            system_prompts = {
                'es': '''Eres Blinky, un asistente amigable y servicial. Tu objetivo es ayudar a los usuarios de manera clara, concisa y amable. 
                Responde en español de manera conversacional y cercana, como un buen amigo que quiere ayudar.''',
                'en': '''You are Blinky, a friendly and helpful assistant buddy. Your goal is to help users in a clear, concise, and kind way.
                Respond in English in a conversational and warm manner, like a good friend who wants to help.''',
                'pt': '''Você é Blinky, um assistente amigável e prestativo. Seu objetivo é ajudar os usuários de forma clara, concisa e gentil.
                Responda em português de maneira conversacional e calorosa, como um bom amigo que quer ajudar.'''
            }
            
            system_prompt = system_prompts.get(language, system_prompts['es'])
            
            # Add length instruction based on max_output_tokens
            length_instructions = {
                'es': f'Mantén tu respuesta concisa (máximo {max_output_tokens} tokens, aproximadamente {int(max_output_tokens * 0.75)} palabras).',
                'en': f'Keep your response concise (maximum {max_output_tokens} tokens, approximately {int(max_output_tokens * 0.75)} words).',
                'pt': f'Mantenha sua resposta concisa (máximo {max_output_tokens} tokens, aproximadamente {int(max_output_tokens * 0.75)} palavras).'
            }
            length_instruction = length_instructions.get(language, length_instructions['es'])
            
            # Retrieve relevant contexts from RAG corpus if enabled
            rag_context = ""
            if use_rag and self.rag_corpus:
                retrieved_contexts = self.retrieve_relevant_contexts(question)
                if retrieved_contexts:
                    rag_context = "\n\nInformación relevante encontrada:\n"
                    for idx, ctx in enumerate(retrieved_contexts, 1):
                        rag_context += f"\n[{idx}] {ctx['text']}\n"
            
            prompt = f"""{system_prompt}
            {length_instruction}
            
            Contexto de la conversación: {context or 'Nueva conversación'}
            {rag_context}
            
            Pregunta del usuario: {question}
            
            Responde de manera útil y amigable, utilizando la información relevante si está disponible:"""
            
            # Configure generation parameters
            generation_config = {
                "max_output_tokens": max_output_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            error_messages = {
                'es': 'Lo siento, ocurrió un error al procesar tu solicitud.',
                'en': 'Sorry, an error occurred while processing your request.',
                'pt': 'Desculpe, ocorreu um erro ao processar sua solicitação.'
            }
            return error_messages.get(language, error_messages['es'])
    
    def get_corpus_info(self) -> Optional[Dict]:
        """Get information about the current RAG corpus"""
        if not self.rag_corpus:
            return None
        
        return {
            'name': self.rag_corpus.name,
            'display_name': self.rag_corpus.display_name,
            'description': self.rag_corpus.description if hasattr(self.rag_corpus, 'description') else None
        }
