import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
import PyPDF2

# --- IMPORTACIONES PARA EL EXPLORADOR DE ARCHIVOS ---
import tkinter as tk
from tkinter import filedialog

# --- IMPORTACIONES PARA PROGRESO ---
import threading
import time
import itertools
from tqdm import tqdm  # --- MODIFICADO: Re-añadimos tqdm ---
# ----------------------------------------------


# --- FUNCIÓN HELPER PARA EL SPINNER (usada en 'ask') ---
def _run_spinner(stop_event, message="🔍 Pensando..."):
    """Función para mostrar un spinner en la consola en un hilo separado."""
    spinner = itertools.cycle(['-', '/', '|', '\\'])
    while not stop_event.is_set():
        # \r mueve el cursor al inicio de la línea
        # flush=True asegura que se imprima inmediatamente
        print(f"\r{message} {next(spinner)}", end="", flush=True)
        time.sleep(0.1)
    # Limpiar la línea al terminar
    print("\r" + " " * (len(message) + 5) + "\r", end="", flush=True)
# --------------------------------------------


# Cargar variables de entorno desde el archivo .env
load_dotenv()

class GeminiRAG:
    def __init__(self, api_key: str):
        """
        Inicializa el sistema RAG con Gemini
        
        Args:
            api_key: Tu API Key de Google Gemini
        """
        self.api_key = api_key
        
        # Inicializar el modelo de embeddings (sin task_type)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        # Inicializar Gemini (usando google_api_key en lugar de api_key)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.3,
            google_api_key=api_key
        )
        
        self.vectorstore = None
        self.qa_chain = None
        
    def load_document(self, file_path: str):
        """
        Carga un documento PDF o TXT usando PyPDF2 directamente
        
        Args:
            file_path: Ruta al archivo PDF o TXT
        """
        print(f"Cargando documento: {file_path}")
        
        documents = []
        
        # Detectar el tipo de archivo
        if file_path.lower().endswith('.pdf'):
            # Usar PyPDF2 directamente para PDFs
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                print(f"📄 PDF detectado con {num_pages} páginas")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    # Crear un documento de Langchain para cada página
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": file_path,
                            "page": page_num + 1
                        }
                    )
                    documents.append(doc)
                    
        elif file_path.lower().endswith('.txt'):
            # Leer archivo TXT
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": file_path
                    }
                )
                documents.append(doc)
        else:
            raise ValueError("Solo se admiten archivos PDF o TXT")
        
        print(f"✅ Documento cargado: {len(documents)} página(s)")
        
        return documents
    
    # --- MÉTODO MODIFICADO ---
    def create_vectorstore(self, documents):
        """
        Crea el vectorstore a partir de los documentos, usando lotes.
        
        Args:
            documents: Lista de documentos cargados
        """
        print("\n📊 Dividiendo el documento en chunks...")
        
        # Dividir el texto en chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        texts = text_splitter.split_documents(documents)
        
        if not texts:
            print("⚠️ No se encontraron chunks de texto para vectorizar.")
            return

        print(f"✅ Documento dividido en {len(texts)} chunks")
        print("\n🔄 Creando vectorstore con embeddings...")

        # --- INICIO: LÓGICA DE LOTES CON TQDM ---
        batch_size = 50  # Puedes ajustar este tamaño
        
        # 1. Inicializar el vectorstore con el primer lote
        try:
            first_batch = texts[:batch_size]
            self.vectorstore = FAISS.from_documents(first_batch, self.embeddings)
            
            # 2. Procesar el resto en lotes con barra de progreso
            remaining_texts = texts[batch_size:]
            
            if remaining_texts:
                # Crear la barra de progreso con el total correcto
                with tqdm(total=len(remaining_texts), desc="⚙️  Vectorizando chunks", unit="chunk") as pbar:
                    # Iterar en pasos del tamaño de batch_size
                    for i in range(0, len(remaining_texts), batch_size):
                        # Obtener el lote actual
                        batch = remaining_texts[i:i + batch_size]
                        
                        # Añadir el lote al vectorstore (esto hace la llamada a la API)
                        self.vectorstore.add_documents(batch)
                        
                        # Actualizar la barra de progreso por el número de chunks procesados
                        pbar.update(len(batch))
                        
        except Exception as e:
            print(f"\n❌ Error durante la vectorización: {e}")
            raise  # Relanzar la excepción para detener la ejecución

        # --- FIN: LÓGICA DE LOTES ---
        
        print("✅ Vectorstore creado exitosamente")
        
    def setup_qa_chain(self):
        """
        Configura la cadena de pregunta-respuesta
        """
        # Plantilla de prompt personalizada en español
        template = """Eres un asistente útil que responde preguntas basándose en el contexto proporcionado.

        Usa la siguiente información de contexto para responder la pregunta.
        Si no sabes la respuesta basándote en el contexto, simplemente di que no tienes suficiente información.
        No inventes información que no esté en el contexto.
        Proporciona una respuesta clara, detallada y bien estructurada en el idioma de la pregunta.

        Contexto: {context}

        Pregunta: {question}

        Respuesta detallada:"""
        
        PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Crear la cadena de QA
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 5}  # Recuperar los 5 chunks más relevantes
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        print("✅ Cadena de QA configurada")
    
    def ask(self, question: str, show_sources: bool = False):
        """
        Hace una pregunta sobre el documento
        
        Args:
            question: La pregunta a realizar
            show_sources: Si True, muestra los fragmentos de texto usados
            
        Returns:
            dict: Diccionario con la respuesta y documentos fuente
        """
        if self.qa_chain is None:
            raise ValueError("Primero debes cargar un documento y configurar el sistema")
        
        print(f"\n🤔 Pregunta: {question}")
        
        # --- Spinner de "Pensando" (aquí sí tiene sentido) ---
        stop_event = threading.Event()
        spinner_thread = threading.Thread(
            target=_run_spinner, 
            args=(stop_event, "🔍 Buscando respuesta...")
        )
        
        result_container = {}

        def qa_work():
            """Función que ejecuta la tarea pesada (llamada a la API)"""
            try:
                result = self.qa_chain.invoke({"query": question})
                result_container['result'] = result
            except Exception as e:
                result_container['error'] = e

        # Iniciar los hilos
        qa_thread = threading.Thread(target=qa_work)
        spinner_thread.start()
        qa_thread.start()
        
        qa_thread.join()
        
        stop_event.set()
        spinner_thread.join()
        
        if 'error' in result_container:
            raise result_container['error']
            
        if 'result' not in result_container:
             raise Exception("No se obtuvo respuesta (error desconocido en el hilo)")
             
        result = result_container['result']
        # --- FIN Spinner ---
        
        response = {
            "answer": result["result"],
            "source_documents": result["source_documents"]
        }
        
        if show_sources and result["source_documents"]:
            print("\n📚 Fragmentos de texto utilizados:")
            for i, doc in enumerate(result["source_documents"], 1):
                print(f"\n--- Fuente {i} ---")
                print(doc.page_content[:200] + "...")
        
        return response
    
    def process_file(self, file_path: str):
        """
        Procesa un archivo completo: carga, vectoriza y configura QA
        
        Args:
            file_path: Ruta al archivo PDF o TXT
        """
        documents = self.load_document(file_path)
        self.create_vectorstore(documents)
        
        # Si el vectorstore no se creó (ej. no había texto), no continuar
        if not self.vectorstore:
            print("❌ No se pudo crear el vectorstore. Abortando.")
            return False # Indicar fallo
            
        self.setup_qa_chain()
        print("\n" + "="*80)
        print("✅ Sistema RAG listo para responder preguntas")
        print("="*80 + "\n")
        return True # Indicar éxito


# Ejemplo de uso
if __name__ == "__main__":
    # Configura tu API Key de Gemini
    API_KEY = os.getenv("GEMINI_API_KEY")
    
    if not API_KEY:
        print("❌ Error: No se encontró la API Key de Gemini")
        print("Configura la variable de entorno GEMINI_API_KEY o edita el código")
        exit(1)
    
    # Configurar la ventana raíz de tkinter (para el diálogo)
    root = tk.Tk()
    root.withdraw() # Ocultar la ventana raíz

    file_types = [
        ("Documentos (PDF, TXT)", "*.pdf *.txt"),
        ("Archivos PDF", "*.pdf"),
        ("Archivos de Texto", "*.txt"),
        ("Todos los archivos", "*.*")
    ]
    
    print("📂 Por favor, selecciona un archivo PDF o TXT para procesar...")
    
    file_path = filedialog.askopenfilename(
        title="Seleccionar documento para RAG",
        filetypes=file_types
    )
    
    if not file_path:
        print("\n❌ No se seleccionó ningún archivo. Saliendo...")
        exit(0) 
        
    print(f"\nArchivo seleccionado: {file_path}")
    
    # Inicializar el RAG
    print("🚀 Inicializando sistema RAG con Gemini...")
    rag = GeminiRAG(api_key=API_KEY)
    
    try:
        # --- MODIFICADO: Comprobar si el procesamiento fue exitoso ---
        success = rag.process_file(file_path)
        
        if success:
            # Hacer preguntas interactivas
            print("💬 Modo interactivo activado. Escribe 'salir' para terminar.\n")
            
            while True:
                question = input("Tu pregunta: ").strip()
                
                if question.lower() in ['salir', 'exit', 'quit', 'q']:
                    print("\n👋 ¡Hasta luego!")
                    break
                
                if not question:
                    continue
                
                try:
                    result = rag.ask(question, show_sources=False)
                    
                    print(f"\n{'='*80}")
                    print(f"💡 Respuesta:\n{result['answer']}")
                    print(f"\n📄 Basado en {len(result['source_documents'])} fragmentos del documento")
                    print(f"{'='*80}\n")
                    
                except Exception as e:
                    print(f"\n❌ Error al procesar la pregunta: {e}\n")
        else:
            print("El programa no puede continuar sin un documento procesado.")
            
    except FileNotFoundError:
        print(f"\n❌ Error: No se encontró el archivo '{file_path}'")
        print("Por favor, verifica que el archivo existe en la ruta especificada")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()