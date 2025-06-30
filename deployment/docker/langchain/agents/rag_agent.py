# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
            from pathlib import Path
            import json
            import os
            import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import logging

            from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader, PDFLoader, JSONLoader
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from utils.logger import setup_logger
"""
RAG Agent
=========

Retrieval-Augmented Generation agent for information retrieval,
context provision, and knowledge-based responses.
"""




logger = setup_logger(__name__)

class RAGAgent:
    """
    Retrieval-Augmented Generation Agent
    
    Capabilities:
    - Document retrieval and analysis
    - Context-aware question answering
    - Knowledge base management
    - Information synthesis
    """
    
    def __init__(self, name: str, memory_manager, vector_store, tool_registry):
        self.name = name
        self.memory_manager = memory_manager
        self.vector_store = vector_store
        self.tool_registry = tool_registry
        
        # LLM for RAG responses
        self.llm = ChatOpenAI()
            model="gpt-4-turbo-preview",
            temperature=0.2,
            max_tokens=2000
        
        
        # Embeddings for vector search
        self.embeddings = OpenAIEmbeddings()
        
        # Document processing
        self.text_splitter = RecursiveCharacterTextSplitter()
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        
        
        # Knowledge base
        self.knowledge_base = None
        self.retrieval_chain = None
        
        # Agent capabilities
        self.capabilities = []
            "document_retrieval",
            "question_answering", 
            "context_synthesis",
            "knowledge_management",
            "information_extraction"
        
        
        self.setup_prompts()
        logger.info(str(f"[SEARCH] RAG Agent '{name}' initialized")

    def setup_prompts(self):
        """Set up RAG-specific prompt templates"""
        
        self.rag_prompt = ChatPromptTemplate.from_messages([)]
            ("system", """You are a specialized RAG (Retrieval-Augmented Generation) agent for a flash loan arbitrage system.)

            Your responsibilities:
            1. Retrieve relevant information from the knowledge base
            2. Synthesize retrieved information with the current context
            3. Provide accurate, contextual responses
            4. Identify information gaps and suggest additional sources
            
            Guidelines:
            - Always cite sources when possible
            - Indicate confidence levels in your responses
            - Highlight when information might be outdated
            - Suggest follow-up queries for better results
            
            Retrieved Context: {context}
            
            Respond with JSON containing:
            - response: Your detailed answer
            - confidence: Float between 0 and 1
            - sources: List of source documents/chunks used
            - related_topics: Suggestions for related information
            - information_gaps: Any missing information identified
            """),
            ("human", "{question}")
        
        
        self.synthesis_prompt = ChatPromptTemplate.from_messages([)]
            ("system", """You are synthesizing information from multiple sources for flash loan arbitrage analysis.)
            
            Your task:
            1. Combine information from different sources
            2. Resolve contradictions where possible
            3. Identify the most reliable sources
            4. Create a coherent summary
            5. Highlight uncertainties and gaps
            
            Consider:
            - Source credibility and recency
            - Data consistency across sources  
            - Relevance to the specific query
            - Potential biases in sources
            """),
            ("human", "Sources to synthesize:\n{sources}\n\nQuery: {query}")
        

    async def initialize(self):
        """Initialize the RAG agent"""
        try:
            logger.info(str(f"[SEARCH] Initializing RAG Agent '{self.name}'...")
            
            # Initialize knowledge base
            await self.setup_knowledge_base()
            
            # Setup retrieval chain
            await self.setup_retrieval_chain()
            
            logger.info(str(f"[OK] RAG Agent '{self.name}' initialization completed")
            
        except Exception as e:
            logger.error(str(f"[ERROR] RAG Agent initialization failed: {e}")
            raise

    async def setup_knowledge_base(self):
        """Set up the vector knowledge base"""
        try:
            # Initialize vector store if not already done
            if not self.knowledge_base:
                self.knowledge_base = await self.vector_store.get_collection("flash_loan_knowledge")
            
            # Load initial documents if knowledge base is empty
            if await self.is_knowledge_base_empty():
                await self.load_initial_documents()
            
            logger.info("[OK] Knowledge base setup completed")
            
        except Exception as e:
            logger.error(str(f"[ERROR] Knowledge base setup failed: {e}")
            raise

    async def setup_retrieval_chain(self):
        """Set up the retrieval chain for QA"""
        try:
            if self.knowledge_base:
                retriever = self.knowledge_base.as_retriever()
                    search_type="similarity",
                    search_kwargs={"k": 5}
                
                
                self.retrieval_chain = RetrievalQA.from_chain_type()
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=True
                
            
            logger.info("[OK] Retrieval chain setup completed")
            
        except Exception as e:
            logger.error(str(f"[ERROR] Retrieval chain setup failed: {e}")
            raise

    async def is_knowledge_base_empty(self) -> bool:
        """Check if the knowledge base is empty"""
        try:
            # This would need to be implemented based on your vector store
            return True  # Placeholder
        except Exception as e:
            logger.error(str(f"[ERROR] Failed to check knowledge base status: {e}")
            return True

    async def load_initial_documents(self):
        """Load initial documents into the knowledge base"""
        try:
            logger.info("📚 Loading initial documents...")
            
            # Define document sources
            document_sources = []
                "/app/data/flash_loan_docs/",
                "/app/data/defi_protocols/",
                "/app/data/arbitrage_strategies/",
                "/app/data/risk_management/",
                "/app/data/market_analysis/"
            
            
            # Load and process documents
            all_documents = []
            for source in document_sources:
                try:
                    docs = await self.load_documents_from_path(source)
                    all_documents.extend(docs)
                except Exception as e:
                    logger.warning(str(f"[WARN] Could not load documents from {source}: {e}")
            
            if all_documents:
                # Split documents into chunks
                chunks = self.text_splitter.split_documents(all_documents)
                
                # Add to vector store
                await self.vector_store.add_documents(chunks)
                
                logger.info(str(f"[OK] Loaded {len(all_documents} documents ({len(chunks)} chunks)")))
            else:
                logger.warning("[WARN] No documents found to load")
                
        except Exception as e:
            logger.error(str(f"[ERROR] Failed to load initial documents: {e}")

    async def load_documents_from_path(self, path: str) -> List:
        """Load documents from a given path"""
        try:
            
            documents = []
            if os.path.exists(path):
                for file_path in Path(path).rglob("*"):
                    if file_path.is_file():
                        try:
                            if file_path.suffix.lower() == '.txt':
                                loader = TextLoader(str(file_path))
                            elif file_path.suffix.lower() == '.pdf':
                                loader = PDFLoader(str(file_path))
                            elif file_path.suffix.lower() == '.json':
                                loader = JSONLoader(str(file_path))
                            else:
                                continue
                                
                            docs = loader.load()
                            documents.extend(docs)
                            
                        except Exception as e:
                            logger.warning(str(f"[WARN] Could not load {file_path}: {e}")
            
            return documents
            
        except Exception as e:
            logger.error(str(f"[ERROR] Failed to load documents from {path}: {e}")
            return []

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process RAG requests within the agent workflow"""
        try:
            messages = state.get("messages", [])
            context = state.get("context", {})
            
            if not messages:
                return state
            
            # Get the latest message
            latest_message = messages[-1]
            query = latest_message.content if hasattr(latest_message, 'content') else str(latest_message)
            
            logger.info(str(f"[SEARCH] Processing RAG query: {query[:100]}...")
            
            # Perform RAG retrieval and generation
            result = await self.retrieve_and_generate(query, context)
            
            # Create response message
            response_msg = AIMessage()
                content=f"RAG Analysis: {result.get('response', 'No response generated')}"
            
            state["messages"].append(response_msg)
            
            # Update result
            state["result"] = result
            
            return state
            
        except Exception as e:
            logger.error(str(f"[ERROR] RAG processing failed: {e}")
            error_msg = AIMessage(content=f"RAG error: {str(e)}")
            state["messages"].append(error_msg)
            return state

    async def process_direct(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a direct RAG query"""
        try:
            return await self.retrieve_and_generate(query, context)
            
        except Exception as e:
            logger.error(str(f"[ERROR] Direct RAG processing failed: {e}")
            return {}
                "response": f"RAG processing error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            

    async def retrieve_and_generate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform retrieval and generation"""
        try:
            # Retrieve relevant documents
            retrieved_docs = await self.retrieve_documents(query, context)
            
            # Generate response using retrieved context
            response = await self.generate_response(query, retrieved_docs, context)
            
            return response
            
        except Exception as e:
            logger.error(str(f"[ERROR] Retrieve and generate failed: {e}")
            return {}
                "response": f"RAG error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            

    async def retrieve_documents(self, query: str, context: Dict[str, Any]) -> List[Dict]:
        """Retrieve relevant documents from the knowledge base"""
        try:
            if not self.retrieval_chain:
                logger.warning("[WARN] Retrieval chain not initialized, using fallback")
                return []
            
            # Perform retrieval
            result = await self.retrieval_chain.ainvoke({"query": query})
            
            # Extract source documents
            source_docs = result.get("source_documents", [])
            
            # Format retrieved documents
            retrieved_docs = []
            for doc in source_docs:
                retrieved_docs.append({)}
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": getattr(doc, 'relevance_score', 0.5)
                
            
            logger.info(str(f"[SEARCH] Retrieved {len(retrieved_docs} relevant documents")
            return retrieved_docs
            
        except Exception as e:
            logger.error(str(f"[ERROR] Document retrieval failed: {e}")
            return []

    async def generate_response(self, query: str, retrieved_docs: List[Dict], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response using retrieved documents"""
        try:
            # Prepare context from retrieved documents
            doc_context = "\n\n".join([)]
                f"Source {i+1}:\n{doc['content']}\nMetadata: {doc['metadata']}"
                for i, doc in enumerate(retrieved_docs)
            
            
            # Prepare prompt
            prompt_input = {}
                "question": query,
                "context": doc_context
            
            
            # Generate response
            response = await self.llm.ainvoke()
                self.rag_prompt.format_messages(**prompt_input)
            
            
            # Parse response
            parsed_response = self.parse_rag_response(response.content)
            
            # Add metadata
            parsed_response["metadata"].update({)}
                "retrieved_docs_count": len(retrieved_docs),
                "query": query,
                "timestamp": datetime.now().isoformat()
            
            
            return parsed_response
            
        except Exception as e:
            logger.error(str(f"[ERROR] Response generation failed: {e}")
            return {}
                "response": f"Response generation error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            

    def parse_rag_response(self, response: str) -> Dict[str, Any]:
        """Parse the RAG response"""
        try:
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {}
                    "response": parsed.get("response", response),
                    "confidence": parsed.get("confidence", 0.5),
                    "metadata": {}
                        "sources": parsed.get("sources", []),
                        "related_topics": parsed.get("related_topics", []),
                        "information_gaps": parsed.get("information_gaps", [])
                    
                
            
            # Fallback parsing
            return {}
                "response": response,
                "confidence": 0.5,
                "metadata": {"parsing_method": "fallback"}
            
            
        except Exception as e:
            logger.error(str(f"[ERROR] Failed to parse RAG response: {e}")
            return {}
                "response": response,
                "confidence": 0.3,
                "metadata": {"error": str(e)}
            

    async def add_document(self, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a new document to the knowledge base"""
        try:
            # Create document
            
            doc = Document()
                page_content=content,
                metadata=metadata or {}
            
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Add to vector store
            await self.vector_store.add_documents(chunks)
            
            logger.info(str(f"[OK] Added document with {len(chunks} chunks to knowledge base")
            return True
            
        except Exception as e:
            logger.error(str(f"[ERROR] Failed to add document: {e}")
            return False

    async def search_knowledge_base(self, query: str, k: int = 5) -> List[Dict]:
        """Search the knowledge base directly"""
        try:
            if not self.knowledge_base:
                logger.warning("[WARN] Knowledge base not initialized")
                return []
            
            # Perform similarity search
            results = await self.knowledge_base.asimilarity_search(query, k=k)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({)}
                    "content": result.page_content,
                    "metadata": result.metadata,
                    "score": getattr(result, 'score', 0.0)
                
            
            return formatted_results
            
        except Exception as e:
            logger.error(str(f"[ERROR] Knowledge base search failed: {e}")
            return []