import chromadb
from chromadb.utils import embedding_functions
import os

# Setup persistent storage in your rag_pipeline folder
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Using a standard lightweight embedding model
default_ef = embedding_functions.DefaultEmbeddingFunction()

def ingest_knowledge_base(domain):
    """Reads .txt files and stores them in ChromaDB."""
    filename = "symptoms_db.txt" if domain == "healthcare" else "loan_products.txt"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    if not os.path.exists(filepath):
        return f"Error: {filename} not found."

    collection = client.get_or_create_collection(name=domain, embedding_function=default_ef)
    
    with open(filepath, "r") as f:
        content = f.read().split("\n\n") # Split by clusters
        
    ids = [f"{domain}_{i}" for i in range(len(content))]
    collection.add(documents=content, ids=ids)
    return f"✅ {domain} knowledge base ingested."

async def get_context(query, domain):
    """Searches ChromaDB for the most relevant info based on user query."""
    try:
        collection = client.get_collection(name=domain, embedding_function=default_ef)
    except:
        # If collection doesn't exist, ingest it first
        ingest_knowledge_base(domain)
        collection = client.get_collection(name=domain, embedding_function=default_ef)

    results = collection.query(query_texts=[query], n_results=1)
    return results['documents'][0][0] if results['documents'] else "No relevant context found."