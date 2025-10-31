import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter

class RAGService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name=groq_model
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        self.vector_store = None
        self.qa_chain = None

    def load_collection(self, collection_path):
        collection_path = f"data/collections/{collection_path}"

        loader = DirectoryLoader(
            collection_path,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )

        documents = loader.load()

        if not documents:
            return False
        
        texts = self.text_splitter.split_documents(documents)

        self.vector_store = FAISS.from_documents(texts, self.embeddings)

        template = """
            Use os seguintes documentos para responder a pergunta.
            Se a resposta não estiver nos documentos, diga que não sabe.

            {context}

            Pergunta: {question}   
        """

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        def _format_docs(docs):
            return "\n\n".join(d.page_content for d in docs)

        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        # LCEL chain: {question} -> {context, question} -> prompt -> llm -> string
        self.qa_chain = (
            {
                "context": itemgetter("question") | retriever | _format_docs,
                "question": itemgetter("question"),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return True
    
    def ask_question(self, question):
        """Faz pergunta ao RAG"""
        if not self.qa_chain:
            return "Nenhuma coleção carregada."
        
        try:
            result = self.qa_chain.invoke({"question": question})
            return result
        except Exception as e:
            return f"Erro ao processar a pergunta: {str(e)}"