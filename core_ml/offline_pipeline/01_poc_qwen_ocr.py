import os
from pathlib import Path
import ollama

def procesar_imagenes_con_qwen():
    # rutas
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_dir = base_dir / "data" / "raw" / "poc_ocr"
    output_dir = base_dir / "data" / "processed" / "poc_ocr"
    
    # si no existe la carpeta de salida, crearla
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # El modelo exacto que descargaste en Ollama
    MODELO = 'qwen3-vl:8b' 
    
    # prompt estricto para forzar el comportamiento de OCR a Markdown
    SYSTEM_PROMPT = (
        "Eres un experto en extracción de datos y maquetación documental. "
        "Tu única tarea es convertir esta imagen escaneada del manual de tesis "
        "en un documento Markdown estricto. "
        "Reglas:\n"
        "1. Mantén toda la información original intacta.\n"
        "2. Convierte los títulos en jerarquías Markdown (#, ##, ###).\n"
        "3. Convierte las tablas fielmente en formato de tabla Markdown.\n"
        "4. Omite números de página, marcas de agua o encabezados repetitivos "
        "que no aporten valor al contenido estructural.\n"
        "5. Devuelve ÚNICAMENTE el código Markdown, sin introducciones ni conclusiones."
    )

    # obtener la lista de imágenes en la carpeta input
    extensiones_validas = {'.png', '.jpg', '.jpeg'}
    imagenes = [f for f in input_dir.iterdir() if f.suffix.lower() in extensiones_validas]
    
    if not imagenes:
        print(f"No se encontraron imágenes en: {input_dir}")
        return

    print(f"Iniciando POC de OCR con {MODELO}. Imágenes a procesar: {len(imagenes)}\n")

    # iterar y procesar cada imagen
    for img_path in sorted(imagenes):
        print(f"Procesando: {img_path.name}...")
        
        try:
            # llamada a ollama con el prompt y la imagen
            response = ollama.chat(
                model=MODELO,
                messages=[
                    {
                        'role': 'user',
                        'content': SYSTEM_PROMPT,
                        'images': [str(img_path)]
                    }
                ]
            )
            
            # extraer el contenido md
            markdown_generado = response.get('message', {}).get('content', '')
            
            # guardar el resultado md con el mismo nombre
            output_filename = f"{img_path.stem}_extraido.md"
            output_path = output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_generado)
                
            print(f"  [ÉXITO] Guardado en: {output_path.relative_to(base_dir)}\n")
            
        except Exception as e:
            print(f"  [ERROR] Falló el procesamiento de {img_path.name}. Detalle: {e}\n")

    print("Pipeline de prueba finalizado. Revisa la carpeta procesada.")

if __name__ == "__main__":
    procesar_imagenes_con_qwen()