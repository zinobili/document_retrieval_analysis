'''
pip install langchain
pip install sentence-transformers
pip install faiss-cpu
'''
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma, FAISS
from langchain.text_splitter import CharacterTextSplitter

vdb_folder = './static/working_file/vectorDB'

def build_vector_DB(file_path):
    ## pdf to text
    filename=file_path.split('/')[-1].split('.')[0]
    print(f"Converting from {file_path} ...")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    ## using option B text splitter
    text_splitter = splitter_options['b']
    texts = text_splitter.split_documents(documents)

    ## openSource embedding
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2',
                                       model_kwargs={'device': 'cpu'})
    docsearch = FAISS.from_documents(texts, embeddings)

    docsearch.save_local(f"{vdb_folder}/{filename}_faiss_index")
    # new_db = FAISS.load_local("faiss_index", embeddings) ## loading
    return docsearch

def quick_load_a_docsearch(file_path):
    vdb_folder = './static/working_file/vectorDB'
    filename=file_path.split('/')[-1].split('.')[0]
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2',
                                       model_kwargs={'device': 'cpu'})
    docsearch = FAISS.load_local(f"{vdb_folder}/{filename}_faiss_index", embeddings) ## loading
    return docsearch


splitter_options={}
splitter_options['a']=CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
splitter_options['b']=CharacterTextSplitter(
                            separator="\n",
                            chunk_size=1000,
                            chunk_overlap=150,
                            length_function=len
                        )
splitter_options['c']=RecursiveCharacterTextSplitter(
                            chunk_size = 1000,
                            chunk_overlap  = 20,
                            length_function = len,
                        #     separators=["\n", " ", ""]
                        )
splitter_options['d']=RecursiveCharacterTextSplitter(
                            chunk_size = 1000,
                            chunk_overlap  = 20,
                            length_function = len,
                            separators=["\n", " ", ""]
                        )