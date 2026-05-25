import time
from pathlib import Path
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def probar_recuperacion():
    base_dir = Path(__file__).resolve().parent.parent.parent
    persist_dir = base_dir / "data" / "vector_db"
    
    # carga del modelo de embeddings (usara cache local)
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-m3",
        device="cuda"
    )
    Settings.embed_model = embed_model
    Settings.llm = None
    
    print("Cargando base de datos vectorial desde disco...")
    if not persist_dir.exists():
        print(f"Error: No se encontro el directorio persistido en {persist_dir}")
        return
        
    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
    index = load_index_from_storage(storage_context)
    
    retriever = index.as_retriever(similarity_top_k=3)
    
    query = "Tipos de fuentes de datos para estudios cuantitativos"
    print(f"\nRealizando consulta semantica: '{query}'\n")
    
    start_time = time.time()
    nodos_recuperados = retriever.retrieve(query)
    elapsed = time.time() - start_time
    
    print(f"Busqueda completada en {elapsed:.4f} segundos.\n")
    
    for i, nodo in enumerate(nodos_recuperados, 1):
        score = nodo.score
        texto = nodo.node.text
        metadata = nodo.node.metadata
        
        print(f"--- RESULTADO #{i} (Similitud: {score:.4f}) ---")
        print(f"Headers: {metadata.get('jerarquia_headers')}")
        print(f"Paginas origen: {[p.get('archivo') for p in metadata.get('paginas_origen', [])]}")
        print(f"Texto:\n{texto[:400]}...")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    probar_recuperacion()
