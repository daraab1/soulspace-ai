from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import chromadb  

# initialize chromaDB 
embedding_function = OllamaEmbeddings(model="nomic-embed-text")  

# collection using LangChain's Chroma wrapper
vectorstore = Chroma(
    collection_name="therapy_knowledge",
    embedding_function=embedding_function,
    persist_directory="database"
)

#therapy techniques
techniques = [
    "Deep breathing helps reduce anxiety by activating the parasympathetic nervous system",
    "The 5-4-3-2-1 grounding technique: Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste",
    "Progressive muscle relaxation reduces tension by systematically tensing and relaxing muscle groups",
    "Cognitive reframing: Challenge negative thoughts by asking 'Is this thought helpful or true?'",
    "Brief meditation: Focus on your breath for 3 minutes while acknowledging and releasing thoughts"
]

#Add doc
vectorstore.add_texts(
    texts=techniques,
    ids=[f"doc_{i}" for i in range(1, 6)]
)

#Test query using LangChain
results = vectorstore.similarity_search("anxiety", k=1)
print([doc.page_content for doc in results])

# Export components (modified for LangChain)
__all__ = ['vectorstore', 'embedding_function']