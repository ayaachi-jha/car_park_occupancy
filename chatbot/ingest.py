import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Define paths relative to the project root
KNOWLEDGE_BASE_DIR = "knowledge_base"
FAISS_INDEX_PATH = "faiss_index"

def create_vector_db():
    """
    Creates a FAISS vector database from documents in the knowledge base directory.
    """
    print(f"Loading documents from '{KNOWLEDGE_BASE_DIR}'...")

    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"Error: Knowledge base directory not found at '{KNOWLEDGE_BASE_DIR}'.")
        print("Please make sure the directory exists and contains your .txt files.")
        return

    loader = DirectoryLoader(
        KNOWLEDGE_BASE_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        show_progress=True,
        use_multithreading=True
    )
    documents = loader.load()

    if not documents:
        print("No .txt documents found in the knowledge base. Exiting.")
        return

    print(f"Loaded {len(documents)} documents.")

    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} chunks.")

    print("Loading sentence transformer embedding model (this may download the model on first run)...")
    embeddings = HuggingFaceEmbeddings(
        model_name='all-MiniLM-L6-v2',
        model_kwargs={'device': 'cpu'}
    )

    print("Creating FAISS vector store and saving to disk...")
    db = FAISS.from_documents(texts, embeddings)

    db.save_local(FAISS_INDEX_PATH)

    print("--------------------------------------------------")
    print(f"Vector database created and saved at: '{FAISS_INDEX_PATH}'")
    print("You can now use this index in your main application.")
    print("--------------------------------------------------")


if __name__ == "__main__":
    create_vector_db()