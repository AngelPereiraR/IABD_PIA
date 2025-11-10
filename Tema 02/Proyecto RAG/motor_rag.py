import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, AIMessage

# Cargar variables de entorno
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FAISS_INDEX_PATH = "faiss_index_tea"

class TeaRagEngine:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY no encontrada en variables de entorno.")

        # Usamos una lista de mensajes de LangChain para el historial
        self.chat_history = []

        # 1. Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=GEMINI_API_KEY
        )

        # 2. Vector Store
        try:
            self.vectorstore = FAISS.load_local(
                FAISS_INDEX_PATH, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            raise FileNotFoundError(f"No se pudo cargar el índice FAISS. Error: {e}")

        # 3. LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=GEMINI_API_KEY
        )

        # 4. Configurar Cadena Completa
        self.rag_chain = self._setup_rag_chain()

    def _setup_rag_chain(self):
        # --- A. RETRIEVER CON CONCIENCIA DE HISTORIAL ---
        # Este prompt le dice al LLM cómo reformular la pregunta basándose en el historial.
        contextualize_q_system_prompt = """Dado un historial de chat y la última pregunta del usuario 
        (que podría hacer referencia al contexto del historial), formula una pregunta independiente 
        que pueda entenderse sin el historial. NO respondas a la pregunta, 
        simplemente reformúlala si es necesario o devuélvela tal cual si ya es clara."""
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 10})
        
        # Cadena intermedia que reformula la pregunta antes de buscar
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        # --- B. CADENA DE RESPUESTA (QA) ---
        # Prompt para generar la respuesta final usando los documentos recuperados.
        qa_system_prompt = """Eres un asistente virtual especializado en TEA en Andalucía.
        Usa los siguientes fragmentos de contexto recuperado para responder a la pregunta.
        Si no sabes la respuesta, di honestamente que no tienes información suficiente.
        Usa un tono cercano y claro.

        {context}"""
        
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        # --- C. CADENA FINAL RAG ---
        # Conecta el retriever inteligente con la cadena de respuesta
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        return rag_chain

    def get_answer(self, query):
        """
        Procesa una pregunta teniendo en cuenta el historial.
        """
        # Invocar la cadena con el historial actual en formato de mensajes
        result = self.rag_chain.invoke({
            "input": query,
            "chat_history": self.chat_history
        })

        # Actualizar historial con tipos de mensaje correctos
        self.chat_history.extend([
            HumanMessage(content=query),
            AIMessage(content=result["answer"]),
        ])
        
        # Mantener el historial manejable (últimos 10 mensajes = 5 pares)
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]

        return {
            "answer": result["answer"],
            "source_documents": result["context"]
        }
    
    def clear_history(self):
        self.chat_history = []

if __name__ == "__main__":
    try:
        engine = TeaRagEngine()
        print("✅ Motor RAG inicializado (History-Aware Retriever).")
        
        # Prueba de la casuística problemática
        q1 = "¿Qué es el CVO?"
        print(f"\n>>> Pregunta 1: {q1}")
        r1 = engine.get_answer(q1)
        print(f"Respuesta 1: {r1['answer'][:200]}...")

        q2 = "¿Y dónde está el de Sevilla?" 
        # AHORA DEBERÍA FUNCIONAR: El modelo reformulará internamente a 
        # "¿Dónde está el Centro de Valoración y Orientación (CVO) de Sevilla?" antes de buscar.
        print(f"\n>>> Pregunta 2 (Contextual): {q2}")
        r2 = engine.get_answer(q2)
        print(f"Respuesta 2: {r2['answer'][:200]}...")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")