import os
import re
from pathlib import Path

def a_romano(num):
    """Convierte un número entero a número romano en minúsculas para los preliminares."""
    valores = [
        (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')
    ]
    resultado = []
    for valor, letra in valores:
        while num >= valor:
            resultado.append(letra)
            num -= valor
    return ''.join(resultado)

def normalizar_paginas_manual():
    # rutas
    base_dir = Path(__file__).resolve().parent.parent.parent
    # carpeta origen
    input_base_dir = base_dir / "data" / "processed" / "poc_ocr"
    
    # carpeta destino
    output_dir = base_dir / "data" / "processed" / "paginas_normalizadas_v2"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    
    # cantidad de pags de cada pdf
    PAGINAS_POR_CARPETA = {
        1: 165,  
        2: 165,  
        3: 165,  
        4: 71   
    }

    # desfase en el contenido del manual por las pags preliminaeres (portada, índice, etc..)
    DESFASE_PAGINAS = 26 

    # expresion regular para capturar el num local de los archivos. por ejmplo "pag_103"
    patron_pagina = re.compile(r"pag_(\d+)")
    archivos_procesados = 0

    print("Iniciando normalización e inyección de metadatos de usuario final...\n")

    # calculo del indice absoluto de cada pag y renombramiento
    for carpeta_num, total_paginas in PAGINAS_POR_CARPETA.items():
        carpeta_path = input_base_dir / str(carpeta_num)
        
        if not carpeta_path.exists():
            print(f"  [ADVERTENCIA] No se encontró la carpeta {carpeta_num}. Saltando...")
            continue

        # calculo de cuantas pags hay acumuladas en las carpetas anteriores
        offset = sum(PAGINAS_POR_CARPETA[i] for i in range(1, carpeta_num))
        archivos_md = [f for f in carpeta_path.iterdir() if f.suffix == '.md']
        
        print(f"-> Estandarizando carpeta {carpeta_num}/4 ({len(archivos_md)} archivos)...")

        for archivo_path in archivos_md:
            match = patron_pagina.search(archivo_path.name)
            if match:
                pagina_local = int(match.group(1))
                
                # indice real absoluto del archivo (visor del pdf)
                pagina_absoluta = offset + pagina_local 
                
                # calculo de la pag impresa y doble metadato
                if pagina_absoluta <= DESFASE_PAGINAS:
                    # es una pag preliminar, se usa numeracion romana
                    romano = a_romano(pagina_absoluta)
                    nombre_archivo_final = f"preliminar_{romano}.md"
                    etiqueta_metadato = f"> [!INFO] Documento: Manual de Trabajo de Grado UNITEC | Sección: Preliminares | Página PDF: {pagina_absoluta} | Página Impresa: {romano}\n\n"
                else:
                    # es contenido real, se usa nums arabigos
                    numero_impreso = pagina_absoluta - DESFASE_PAGINAS
                    nombre_archivo_final = f"pagina_{numero_impreso}.md"
                    etiqueta_metadato = f"> [!INFO] Documento: Manual de Trabajo de Grado UNITEC | Página PDF: {pagina_absoluta} | Página Impresa: {numero_impreso}\n\n"
                
                # lee el archivo original
                with open(archivo_path, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    
                # limpia artefactos clasicos de Qwen-VL
                contenido = contenido.replace("```markdown\n", "").replace("```", "").strip()

                # fusion del texto con su cabecera
                contenido_final = etiqueta_metadato + contenido

                # guarda el archivo con su nombre estandarizado en la nueva carpeta
                nuevo_path = output_dir / nombre_archivo_final
                
                with open(nuevo_path, 'w', encoding='utf-8') as f:
                    f.write(contenido_final)
                    
                archivos_procesados += 1
            else:
                print(f"  [ADVERTENCIA] Formato no reconocido, se omitirá: {archivo_path.name}")

    print(f"\n¡Arquitectura de datos lista! {archivos_procesados} páginas guardadas en: {output_dir.relative_to(base_dir)}")
    print("Revisa la carpeta 'paginas_normalizadas' para comprobar la estructura.")

if __name__ == "__main__":
    normalizar_paginas_manual()