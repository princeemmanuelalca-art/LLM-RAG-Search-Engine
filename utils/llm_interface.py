"""
LLM Interface: Handles interactions with language models.
Supports OpenAI, Anthropic, Google Gemini, and Groq models.
FIXED: Context builder now shows source filename + page instead of
       "Document 1, Document 2" which confused the LLM into thinking
       multiple documents existed when only one file was uploaded.
"""
from typing import List, Dict
from utils.config import Config

class LLMInterface:
    """Interface for interacting with Large Language Models"""

    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.model = Config.LLM_MODEL

        if self.provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.client = genai.GenerativeModel('models/gemini-2.0-flash-lite')
            self.model = 'gemini-2.0-flash-lite'
        elif self.provider == 'openai':
            from openai import OpenAI
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        elif self.provider == 'anthropic':
            from anthropic import Anthropic
            self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        elif self.provider == 'groq':
            from groq import Groq
            self.client = Groq(api_key=Config.GROQ_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        print(f"LLM initialized: {self.provider} - {self.model}")

    def generate_response(self, query: str, context_documents: List[Dict], conversation_history: List[Dict] = None) -> str:
        """Generate a response using the LLM with retrieved context."""
        context = self._build_context(context_documents)
        system_prompt = self._create_system_prompt()
        user_message = self._create_user_message(query, context)

        if self.provider == 'gemini':
            return self._generate_gemini(system_prompt, user_message, conversation_history)
        elif self.provider == 'openai':
            return self._generate_openai(system_prompt, user_message, conversation_history)
        elif self.provider == 'anthropic':
            return self._generate_anthropic(system_prompt, user_message, conversation_history)
        elif self.provider == 'groq':
            return self._generate_groq(system_prompt, user_message, conversation_history)

    def _build_context(self, documents: List[Dict]) -> str:
        """
        Build context string from retrieved chunks.
        Uses filename + chunk index instead of generic Document numbers
        so the LLM does not confuse multiple chunks as multiple files.
        """
        if not documents:
            return "No relevant content found in the indexed documents."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc['metadata'].get('source', 'Unknown file')
            text = doc['text']
            score = doc.get('score', 0)
            context_parts.append(
                f"[Chunk {i} from '{source}' | relevance: {score:.2f}]\n{text}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _create_system_prompt(self) -> str:
        return """You are EduRAG, an academic research assistant that answers questions based strictly on retrieved document chunks.

Rules you must follow:
- Answer ONLY using the provided context chunks. Do not use outside knowledge.
- When citing sources, refer to the filename shown in the chunk header (e.g. 'According to research.pdf...'), NOT as 'Document 1' or 'Document 2'. Multiple chunks may come from the same file.
- If multiple chunks are from the same file, treat them as excerpts from one document — do not imply multiple separate documents exist.
- If the context does not contain enough information to answer, say so honestly.
- Be concise but thorough. Use academic language appropriate for research contexts.
- Do NOT mention confidence levels, statistical intervals, or quantitative metrics unless the user explicitly asks for them."""

    def _create_user_message(self, query: str, context: str) -> str:
        return f"""Context from the knowledge base:

{context}

Question: {query}

Answer based only on the context above:"""

    def _generate_gemini(self, system_prompt: str, user_message: str, conversation_history: List[Dict]) -> str:
        full_prompt = f"{system_prompt}\n\n{user_message}"
        if conversation_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-6:]:
                role = "User" if msg['role'] == 'user' else "Assistant"
                history_text += f"{role}: {msg['content']}\n"
            full_prompt = history_text + "\n" + full_prompt
        try:
            response = self.client.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def _generate_openai(self, system_prompt: str, user_message: str, conversation_history: List[Dict]) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content

    def _generate_anthropic(self, system_prompt: str, user_message: str, conversation_history: List[Dict]) -> str:
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system_prompt,
            messages=messages,
            temperature=0.7
        )
        return response.content[0].text

    def _generate_groq(self, system_prompt: str, user_message: str, conversation_history: List[Dict]) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content

    def simple_chat(self, query: str) -> str:
        """Simple chat without RAG context."""
        if self.provider == 'gemini':
            try:
                response = self.client.generate_content(query)
                return response.text
            except Exception as e:
                return f"Error: {str(e)}"
        elif self.provider == 'openai':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": query}],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        elif self.provider == 'anthropic':
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": query}],
                temperature=0.7
            )
            return response.content[0].text
        elif self.provider == 'groq':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": query}],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content