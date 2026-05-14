import os
import time
from pathlib import Path
import ollama

def procesar_imagenes_con_qwen_optimizado():
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_dir = base_dir / "data" / "raw" / "poc_ocr2"
    output_dir = base_dir / "data" / "processed" / "poc_ocr"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    MODELO = 'qwen3-vl:8b' 
    
    # segundos de enfriamiento entre inferencias para evitar sobrecalentamiento de GPU
    TIEMPO_ENFRIAMIENTO = 15 
    
    SYSTEM_PROMPT = (
        "Eres un experto en extracción de datos y maquetación documental. "
        "Tu única tarea es convertir esta imagen escaneada del manual de tesis "
        "en un documento Markdown estricto. "
        "Reglas:\n"
        "1. Mantén toda la información original intacta.\n"
        "2. Convierte los títulos en jerarquías Markdown (#, ##, ###).\n"
        "3. Convierte las tablas fielmente en formato de tabla Markdown.\n"
        "4. Omite números de página, marcas de agua o encabezados repetitivos.\n"
        "5. Devuelve ÚNICAMENTE el código Markdown, sin introducciones."
    )

    extensiones_validas = {'.png', '.jpg', '.jpeg'}
    imagenes = sorted([f for f in input_dir.iterdir() if f.suffix.lower() in extensiones_validas])
    
    if not imagenes:
        print(f"No se encontraron imágenes en: {input_dir}")
        return

    print(f"Iniciando OCR Optimizado con {MODELO}. Imágenes a procesar: {len(imagenes)}")
    print(f"Pausa de enfriamiento configurada: {TIEMPO_ENFRIAMIENTO}s por imagen.\n")

    for i, img_path in enumerate(imagenes, 1):
        output_filename = f"{img_path.stem}_extraido.md"
        output_path = output_dir / output_filename

        # si el archivo ya exista, saltar
        if output_path.exists():
            print(f"[{i}/{len(imagenes)}] Saltando {img_path.name}... (Ya procesado)")
            continue

        print(f"[{i}/{len(imagenes)}] Inferencia en GPU: {img_path.name}...")
        
        try:
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
            
            markdown_generado = response.get('message', {}).get('content', '')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_generado)
                
            print(f"  [ÉXITO] Guardado.")
            
            # aplicar enfriamiento excp la ultima imagen
            if i < len(imagenes):
                print(f"  [THERMAL] Enfriando GPU por {TIEMPO_ENFRIAMIENTO} segundos...\n")
                time.sleep(TIEMPO_ENFRIAMIENTO)
            
        except Exception as e:
            print(f"  [ERROR] Falló el procesamiento de {img_path.name}. Detalle: {e}\n")

    print("\nPipeline completado exitosamente.")

if __name__ == "__main__":
    procesar_imagenes_con_qwen_optimizado()