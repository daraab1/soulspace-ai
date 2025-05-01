from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.memory import ConversationBufferMemory
from ollama import Client
from utils.response_handler import make_empathic
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Configuration
MODEL = "mistral"
TEMPERATURE = 0.7
EMBEDDING_MODEL = "nomic-embed-text"

# Initialize memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

def get_response(user_input):
    try:
        # Initialize components
        db = Chroma(
            collection_name="therapy_knowledge",
            embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
            persist_directory="database"
        )
        
        # Retrieve context
        results = db.similarity_search(user_input, k=3)
        context = "\n".join(doc.page_content for doc in results)
        
        # Load conversation history
        history = memory.load_memory_variables({})["chat_history"]
        history_str = "\n".join(str(msg) for msg in history)
        
        # Generate response
        client = Client(host='http://localhost:11434')
        prompt = f"""Previous conversation:
        {history_str}
        
        Therapeutic knowledge:
        {context}
        
        Client: {user_input}
        
        Respond with:
        1. Acknowledge previous discussion
        2. 1-2 techniques
        3. One question"""
        
        response = client.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": TEMPERATURE}
        )
        
        # Save to memory
        memory.save_context(
            {"input": user_input},
            {"output": response['message']['content']}
        )
        
        return make_empathic(response['message']['content'])
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return make_empathic("Let me think differently about that...")

if __name__ == "__main__":
    print("Testing RAG system with memory...")
    while True:
        query = input("\nClient: ")
        if query.lower() in ["quit", "exit"]:
            break
        print("Therapist:", get_response(query))

