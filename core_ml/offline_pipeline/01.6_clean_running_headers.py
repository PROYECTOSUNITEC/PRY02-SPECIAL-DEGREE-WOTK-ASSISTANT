import os
import re
from pathlib import Path

def clean_files():
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_dir = base_dir / "data" / "processed" / "paginas_normalizadas_v2"
    
    re_info_tag = re.compile(r"^> \[!INFO\].*$", re.MULTILINE)
    re_capitulo = re.compile(r"^# (?:Capítulo|CAPÍTULO) [IVXLC\d]+(?::.*)?$", re.IGNORECASE)
    re_investigacion = re.compile(r"^# La investigación en los estudios técnicos y profesionales.*$", re.IGNORECASE)
    
    logo_patterns = [
        re.compile(r"^UNITEC$", re.IGNORECASE),
        re.compile(r"^VENEZUELA$", re.IGNORECASE),
        re.compile(r"^UNITEC\s+VENEZUELA$", re.IGNORECASE),
        re.compile(r"^REPÚBLICA BOLIVARIANA DE VENEZUELA$", re.IGNORECASE)
    ]
    
    ultimo_capitulo_visto = None
    
    def sort_key(path):
        name = path.stem
        if name.startswith("pagina_"):
            try:
                return (1, int(name.split("_")[1]))
            except ValueError:
                return (1, name)
        elif name.startswith("preliminar_"):
            return (0, name)
        return (2, name)

    archivos = sorted(list(input_dir.glob("*.md")), key=sort_key)
    
    print(f"Limpiando {len(archivos)} archivos...")
    
    for archivo_path in archivos:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        if not lineas:
            continue
            
        nuevas_lineas = []
        info_tag_line = ""
        contenido_empezado = False
        lineas_procesadas_en_pagina = 0
        
        for linea in lineas:
            linea_clean = linea.strip()
            
            if re_info_tag.match(linea_clean):
                info_tag_line = linea
                continue
            
            if not linea_clean and not contenido_empezado:
                continue
            
            contenido_empezado = True
            
            # limpieza de logo en las primeras 5 lineas
            if lineas_procesadas_en_pagina < 5:
                if any(p.match(linea_clean) for p in logo_patterns):
                    continue
            
            # cabecera estatica
            if lineas_procesadas_en_pagina < 3 and re_investigacion.match(linea_clean):
                continue
            
            # deduplicacion de capitulos
            match_cap = re_capitulo.match(linea_clean)
            if match_cap and lineas_procesadas_en_pagina < 3:
                titulo_normalizado = linea_clean.strip().upper()
                titulo_normalizado = " ".join(titulo_normalizado.split())
                
                if titulo_normalizado == ultimo_capitulo_visto:
                    continue
                else:
                    ultimo_capitulo_visto = titulo_normalizado
                
            nuevas_lineas.append(linea)
            lineas_procesadas_en_pagina += 1
            
        body = "".join(nuevas_lineas).strip()
        body = re.sub(r'\n{3,}', '\n\n', body)
        contenido_final = info_tag_line + "\n\n" + body + "\n"

        with open(archivo_path, 'w', encoding='utf-8') as f:
            f.write(contenido_final)

    print("Limpieza completada.")

if __name__ == "__main__":
    clean_files()
