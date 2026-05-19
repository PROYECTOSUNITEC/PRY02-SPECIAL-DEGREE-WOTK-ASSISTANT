import json
from pathlib import Path

def buscar_nodos():
    base_dir = Path(__file__).resolve().parent.parent.parent
    json_path = base_dir / "data" / "processed" / "nodos_auditados.json"

    if not json_path.exists():
        print(f"Error: No se encontro el archivo: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        nodos = json.load(f)

    print(f"Nodos cargados: {len(nodos)}")
    print("Ingresa el termino a buscar (o 'salir' para terminar):\n")

    while True:
        try:
            query = input("Buscar: ").strip()
            if not query:
                continue
            if query.lower() in ('salir', 'exit', 'q'):
                break

            resultados = []
            for n in nodos:
                if query.lower() in n['texto'].lower() or any(query.lower() in str(val).lower() for val in n['jerarquia_headers'].values()):
                    resultados.append(n)

            print(f"\nResultados: {len(resultados)} nodos.\n")

            for res in resultados[:5]:
                print(f"--- NODO #{res['nodo_id']} ({res['longitud_caracteres']} caracteres) ---")
                print(f"Headers: {res['jerarquia_headers']}")
                print(f"Paginas:")
                for pg in res['paginas_origen']:
                    print(f"  - {pg.get('archivo')}")
                print("\nTexto:")
                print(res['texto'])
                print("-" * 50)
            
            if len(resultados) > 5:
                print(f"... y otros {len(resultados) - 5} nodos.")

        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            break

if __name__ == "__main__":
    buscar_nodos()
