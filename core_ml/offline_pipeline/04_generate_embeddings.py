import json
import time
from pathlib import Path
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def cargar_nodos_desde_json(json_path: Path) -> list[TextNode]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    nodos_llama = []
    for item in data:
        nodo = TextNode(
            text=item["texto"],
            id_=str(item["nodo_id"]),
            metadata={
                "jerarquia_headers": item.get("jerarquia_headers", {}),
                "paginas_origen": item.get("paginas_origen", []),
                "longitud_caracteres": item.get("longitud_caracteres", 0)
            }
        )
        nodos_llama.append(nodo)
        
    return nodos_llama


def generar_embeddings():
    base_dir = Path(__file__).resolve().parent.parent.parent
    json_path = base_dir / "data" / "processed" / "nodos_auditados.json"
    persist_dir = base_dir / "data" / "vector_db"
    
    print("Cargando nodos desde JSON...")
    if not json_path.exists():
        print(f"Error: No se encontro el archivo {json_path}")
        return
        
    nodos = cargar_nodos_desde_json(json_path)
    print(f"Se cargaron {len(nodos)} nodos.")
    
    print("\nConfigurando modelo de embeddings (BAAI/bge-m3 en CUDA)...")
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-m3",
        device="cuda",
        embed_batch_size=64
    )
    
    Settings.embed_model = embed_model
    Settings.llm = None 
    
    print("\nVectorizando nodos y creando VectorStoreIndex...")
    start_time = time.time()
    
    index = VectorStoreIndex(nodes=nodos)
    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Vectorizacion completada en {elapsed:.2f} segundos.")
    print(f"Throughput aproximado: {len(nodos) / elapsed:.2f} nodos/segundo.")
    
    print("\nPersistiendo indice localmente...")
    persist_dir.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(persist_dir))
    print(f"Indice guardado en: {persist_dir}")
    
    print("\nAuditoria de validacion:")
    test_node = nodos[0]
    embedding = test_node.embedding
    if embedding:
        longitud = len(embedding)
        print(f"Nodo ID: {test_node.id_}")
        print(f"Longitud del vector: {longitud} dimensiones (esperado: 1024)")
        print(f"Muestra del vector (primeros 5 valores): {embedding[:5]}")
    else:
        print("Advertencia: El nodo de prueba no tiene un embedding generado.")


if __name__ == "__main__":
    generar_embeddings()
