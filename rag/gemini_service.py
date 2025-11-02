import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service to interact with Google Gemini API
    """
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Use gemini-2.5-flash (free tier model)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Initialized Gemini API with gemini-2.5-flash")
    
    def generate_response(self, query: str, context: str) -> str:
        """
        Generate response using Gemini with RAG context
        
        Args:
            query: User's question
            context: Retrieved context from vector DB
        
        Returns:
            AI-generated response
        """
        try:
            # Create prompt with context
            prompt = f"""You are a helpful AI assistant. Answer the user's question based on the following context.

Context:
{context}

User Question: {query}

Please provide a clear and accurate answer based on the context provided. If the context doesn't contain relevant information, politely say so.

Answer:"""
            
            logger.info(f"Generating response for query: {query[:50]}...")
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            logger.info("Successfully generated response with Gemini")
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def generate_simple_response(self, query: str) -> str:
        """
        Generate response without context (fallback)
        """
        try:
            logger.info("Generating simple response without context")
            response = self.model.generate_content(query)
            return response.text
        except Exception as e:
            logger.error(f"Error generating simple response: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error: {str(e)}"