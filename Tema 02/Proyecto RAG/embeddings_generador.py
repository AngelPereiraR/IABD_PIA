import os
import json
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from tqdm import tqdm

# --- CONFIGURACIÓN ---
# Cargar variables de entorno (.env con GEMINI_API_KEY)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Archivo de entrada con los chunks ya generados
CHUNKS_INPUT_FILE = "chunks_tea_andalucia.jsonl"

# Ruta donde se guardará el índice FAISS
FAISS_INDEX_PATH = "faiss_index_tea"
# -------------------

class ChunkVectorizer:
    def __init__(self, api_key: str):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        self.vectorstore = None

    def load_chunks_as_documents(self, jsonl_path: str):
        """
        Lee el archivo JSONL y convierte cada línea en un objeto Document de LangChain.
        """
        print(f"📂 Cargando chunks desde: {jsonl_path}")
        documents = []
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    chunk_data = json.loads(line)
                    # Creamos el Documento de LangChain
                    # Usamos el texto del chunk como contenido y el resto como metadatos
                    doc = Document(
                        page_content=chunk_data['text'],
                        metadata=chunk_data['metadata']
                    )
                    # Añadimos el ID único del chunk a los metadatos por si acaso
                    doc.metadata['chunk_id'] = chunk_data['id']
                    documents.append(doc)
            
            print(f"✅ Se cargaron {len(documents)} chunks correctamente.")
            return documents
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo {jsonl_path}")
            return []
        except Exception as e:
            print(f"❌ Error cargando chunks: {e}")
            return []

    def create_and_save_vectorstore(self, documents, index_path):
        """
        Genera embeddings para los documentos (chunks) y guarda el índice FAISS.
        """
        if not documents:
            print("⚠️ No hay chunks para vectorizar.")
            return

        print("\n🔄 Generando embeddings y creando índice FAISS...")
        
        # Tamaño del lote para enviar a la API de embeddings
        batch_size = 50 
        
        try:
            # 1. Inicializar el vectorstore con el primer lote
            first_batch = documents[:batch_size]
            print(f"   - Procesando lote inicial ({len(first_batch)} chunks)...")
            self.vectorstore = FAISS.from_documents(first_batch, self.embeddings)
            
            # 2. Procesar el resto en lotes con barra de progreso
            remaining_docs = documents[batch_size:]
            if remaining_docs:
                with tqdm(total=len(remaining_docs), desc="⚙️ Vectorizando", unit="chunk") as pbar:
                    for i in range(0, len(remaining_docs), batch_size):
                        batch = remaining_docs[i:i + batch_size]
                        self.vectorstore.add_documents(batch)
                        pbar.update(len(batch))
            
            # 3. Guardar el índice localmente
            self.vectorstore.save_local(index_path)
            print(f"\n✅ Vectorstore guardado exitosamente en: {index_path}")
            
        except Exception as e:
            print(f"\n❌ Error durante la vectorización: {e}")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ Error: Configura GEMINI_API_KEY en tu archivo .env")
        exit(1)

    if not os.path.exists(CHUNKS_INPUT_FILE):
        print(f"⚠️ No se encontró el archivo de chunks: {CHUNKS_INPUT_FILE}")
        print("Asegúrate de haber ejecutado el script de chunking primero.")
        exit(1)

    vectorizer = ChunkVectorizer(api_key=GEMINI_API_KEY)
    
    # 1. Cargar los chunks ya preparados como Documentos LangChain
    chunk_documents = vectorizer.load_chunks_as_documents(CHUNKS_INPUT_FILE)
    
    # 2. Vectorizar y guardar
    vectorizer.create_and_save_vectorstore(chunk_documents, FAISS_INDEX_PATH)