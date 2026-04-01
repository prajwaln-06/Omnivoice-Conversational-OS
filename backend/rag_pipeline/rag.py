import chromadb
from chromadb.utils import embedding_functions
import os
import pandas as pd  # Added for CSV handling
import hashlib
import os
from groq import Groq

# 1. Initialize Groq (Uses the GROQ_API_KEY from your .env)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 2. Create the Semantic Cache Dictionary
RAG_CACHE = {}

def hash_query(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode()).hexdigest()

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

def ingest_medquad_csv(file_path):
    print("⏳ Loading MedQuAD dataset (this may take a minute)...")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    df = pd.read_csv(file_path)

    # --- ADD THESE TWO LINES FOR CLEANING ---
    df = df.dropna(subset=['question', 'answer']) # Remove empty rows
    df = df.reset_index(drop=True)               # Reset the ID count
    # ----------------------------------------

    # Combine Question and Answer for better retrieval context
    df['combined_text'] = "Question: " + df['question'].astype(str) + "\nAnswer: " + df['answer'].astype(str)
    
    documents = df['combined_text'].tolist()
    metadatas = [{"source": str(row.get('source', 'NIH')), "focus": str(row.get('focus_area', 'General'))} for _, row in df.iterrows()]
    ids = [f"med_{i}" for i in range(len(documents))]

    collection = client.get_or_create_collection(name="healthcare", embedding_function=default_ef)

    print(f"📦 Data cleaned. Starting ingestion of {len(documents)} records...")

    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
            ids=ids[i : i + batch_size]
        )
    print(f"🔥 Success! Indexed {len(documents)} medical records.")

def ingest_banking_csv(file_path):
    """Professional ingestion for large-scale banking datasets."""
    print(f"⏳ Loading Banking dataset from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    # Load and clean
    df = pd.read_csv(file_path)
    df = df.dropna() # Remove any 'nan' values that crash ChromaDB
    
    # Auto-detect columns (Handles different Kaggle formats)
    cols = df.columns.tolist()
    q_col = cols[0] # Usually 'Question' or 'Instruction'
    a_col = cols[1] # Usually 'Answer' or 'Response'
    
    print(f"🔍 Mapping columns: Query -> {q_col}, Info -> {a_col}")

    df['combined_text'] = "Query: " + df[q_col].astype(str) + "\nInfo: " + df[a_col].astype(str)
    
    documents = df['combined_text'].tolist()
    ids = [f"bank_{i}" for i in range(len(documents))]

    # Collection 'banking'
    collection = client.get_or_create_collection(name="banking", embedding_function=default_ef)

    print(f"📦 Starting ingestion of {len(documents)} banking records...")
    
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i : i + batch_size],
            ids=ids[i : i + batch_size]
        )
    print(f"🔥 Success! Indexed {len(documents)} banking records.")

async def get_context(query: str, domain: str) -> str:
    """Searches ChromaDB for the most relevant info based on user query."""
    # Check for empty query
    if not query:
        return ""
    
    # Check semantic cache
    q_hash = hash_query(query)
    if q_hash in RAG_CACHE:
        print("⚡ RAG Cache Hit! Skipping database search.")
        return RAG_CACHE[q_hash]
    
    # Get or create collection
    try:
        collection = client.get_collection(name=domain, embedding_function=default_ef)
    except:
        # If collection doesn't exist, ingest it first
        ingest_knowledge_base(domain)
        collection = client.get_collection(name=domain, embedding_function=default_ef)
    
    # Query the database
    results = collection.query(query_texts=[query], n_results=3)
    retrieved_context = "\n".join(results['documents'][0]) if results['documents'] else "..."
    
    # Save the result to cache before returning
    RAG_CACHE[q_hash] = retrieved_context
    return retrieved_context

async def check_contraindications(medications: list, historical_context: str) -> list:
    """Checks if prescribed medications conflict with the patient's medical history."""
    if not medications or not historical_context:
        return []
        
    prompt = f"""
    You are a clinical safety AI. Check if these medications conflict with the patient's history.
    Medications: {medications}
    History: {historical_context}
    
    If there is a conflict, reply with a short warning string. If safe, reply with "SAFE".
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        result = response.choices[0].message.content.strip()
        return [] if result == "SAFE" else [f"⚠️ {result}"]
    except Exception as e:
        print(f"Contraindication check failed: {e}")
        return []

    