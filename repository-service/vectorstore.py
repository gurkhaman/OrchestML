from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from pathlib import Path
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from dotenv import dotenv_values

SERVICE_DIR = "./data/services"
PERSIST_DIR = "./data/chroma_local_db"
CONFIG = dotenv_values(".env")

class VectorStoreManager:
    def __init__(self, service_dir: str | Path = "./data/services", persist_dir: str | Path = "./data/chroma_local_db"):
        self.service_dir = Path(service_dir)
        self.persist_dir = Path(persist_dir)
        self.config = dotenv_values(".env")
        self.vectorstore = None
        
        # Ensure directories exist
        self.service_dir.mkdir(parents=True, exist_ok=True)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
    def load_documents(self, directory: Path):
        documents = []
        
        directory = Path(directory)
        
        if not directory.exists():
            raise ValueError(f"Directory {directory} does not exist")
        
        if not directory.is_dir():
            raise ValueError(f"{directory} is not a directory")
        
        # Recursive search for markdown files in subdirectories
        md_files = list(directory.glob("**/*.md"))
        print(f"Found {len(md_files)} markdown files in {directory} (recursive)")
        
        for md_file in md_files:
            try:
                loader = UnstructuredMarkdownLoader(str(md_file))
                data = loader.load()
                if data: 
                    # Add repository source info to metadata
                    relative_path = md_file.relative_to(directory)
                    source_repo = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
                    
                    # Enhance metadata with source information
                    data[0].metadata.update({
                        "source": str(md_file),
                        "repository": source_repo,
                        "filename": md_file.name,
                        "relative_path": str(relative_path)
                    })
                    
                    documents.append(data[0])
                    print(f"Loaded: {source_repo}/{md_file.name}")
            except Exception as e:
                print(f"Error loading {md_file.name}: {e}")

        return documents

    def create_chroma_vectorstore(self, documents: list[Document], persist_directory: Path):
        vectorstore = Chroma.from_documents(
            documents=documents, 
            embedding=OpenAIEmbeddings(api_key=self.config["OPENAI_API_KEY"]),
            persist_directory=str(persist_directory)
        )
        
        return vectorstore

    def load_existing_vectorstore(self):
        if self.persist_dir.exists() and self.persist_dir.is_dir():
            if any(self.persist_dir.iterdir()):
                return Chroma(
                    persist_directory=str(self.persist_dir),
                    embedding_function=OpenAIEmbeddings(api_key=self.config["OPENAI_API_KEY"])
                )
        return None
    
    def initialize_vectorstore(self):
        self.vectorstore = self.load_existing_vectorstore()
        return self.vectorstore is not None
    
    def create_new_vectorstore(self):
        documents = self.load_documents(self.service_dir)
        
        if not documents:
            raise ValueError(f"No markdown documents found in {self.service_dir}")
        
        self.vectorstore = self.create_chroma_vectorstore(documents, self.persist_dir)
        return len(documents)
    
    def search(self, query: str, k: int = 4):
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized")
        
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(query)
        return docs
    
    def get_status(self):
        return {
            "initialized": self.vectorstore is not None,
            "persist_dir": str(self.persist_dir),
            "persist_dir_exists": self.persist_dir.exists(),
            "service_dir": str(self.service_dir),
            "service_dir_exists": self.service_dir.exists(),
            "markdown_files_count": len(list(self.service_dir.glob("**/*.md"))) if self.service_dir.exists() else 0
        }
    
    def list_service_files(self):
        if not self.service_dir.exists():
            return []
        
        # Return files with their repository subdirectory
        files = []
        for md_file in self.service_dir.glob("**/*.md"):
            relative_path = md_file.relative_to(self.service_dir)
            source_repo = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
            files.append(f"{source_repo}/{md_file.name}")
        return files
    
    def get_service_dir_info(self):
        """Get detailed info about service directory"""
        return {
            "path": str(self.service_dir),
            "exists": self.service_dir.exists(),
            "is_directory": self.service_dir.is_dir() if self.service_dir.exists() else False,
            "markdown_files": self.list_service_files(),
            "total_files": len(list(self.service_dir.glob("*"))) if self.service_dir.exists() else 0
        }

