import os
import re
import json
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MARCADOR_PAGINA = "<!-- PAGE_BREAK: {archivo} -->"
PATRON_MARCADOR = re.compile(r"<!-- PAGE_BREAK: (.+?) -->")

RE_TITULO_ESTATICO = re.compile(
    r"^#*\s*La investigación en los estudios técnicos y profesionales.*$",
    re.IGNORECASE | re.MULTILINE,
)
RE_CABEZAL_CAPITULO = re.compile(
    r"^#\s*(?:Capítulo|CAPÍTULO)\s+[IVXLCDM\d]+(?:\s*:\s*.*)?$",
    re.IGNORECASE | re.MULTILINE,
)
RE_TITULO_VACIO = re.compile(r"^#+\s*$", re.MULTILINE)
RE_NUMERO_PAGINA = re.compile(r"^\d{1,4}\s*$", re.MULTILINE)
RE_LINEAS_VACIAS_EXCESO = re.compile(r"\n{3,}")
RE_INFO_TAG = re.compile(r"^> \[!INFO\]\s*(.*)$", re.MULTILINE)
RE_LOGO_ARTEFACTOS = re.compile(
    r"^(?:UNITEC|VENEZUELA|UNITEC\s+VENEZUELA|"
    r"REPÚBLICA BOLIVARIANA DE VENEZUELA|"
    r"UNIVERSIDAD TECNOLÓGICA DEL CENTRO|"
    r"J-\d{8}-\d|"
    r"!\[.*?\]\(.*?\))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
RE_JORGE_AUTOR = re.compile(r"^Jorge Enrique Rodríguez Jaimes\s*$", re.MULTILINE)


def limpiar_cabezales(texto: str) -> str:
    texto = RE_TITULO_ESTATICO.sub("", texto)
    # texto = RE_CABEZAL_CAPITULO.sub("", texto)
    texto = RE_TITULO_VACIO.sub("", texto)
    texto = RE_NUMERO_PAGINA.sub("", texto)
    texto = RE_LOGO_ARTEFACTOS.sub("", texto)
    texto = RE_JORGE_AUTOR.sub("", texto)
    texto = RE_LINEAS_VACIAS_EXCESO.sub("\n\n", texto)
    return texto.strip()


def _sort_key_archivo(path: Path) -> tuple:
    nombre = path.stem
    if nombre.startswith("preliminar_"):
        sufijo = name = nombre.split("_", 1)[1]
        valor = _romano_a_entero(sufijo)
        return (0, valor)

    if nombre.startswith("pagina_"):
        try:
            return (1, int(nombre.split("_", 1)[1]))
        except ValueError:
            return (1, 0)

    return (2, 0)


def _romano_a_entero(romano: str) -> int:
    tabla = {
        "i": 1, "v": 5, "x": 10, "l": 50,
        "c": 100, "d": 500, "m": 1000,
    }
    resultado = 0
    romano_lower = romano.lower()
    for i, char in enumerate(romano_lower):
        valor = tabla.get(char, 0)
        if i + 1 < len(romano_lower) and valor < tabla.get(romano_lower[i + 1], 0):
            resultado -= valor
        else:
            resultado += valor
    return resultado


def fusionar_documento_monolitico(input_dir: Path) -> tuple[str, dict[str, str]]:
    # lee, limpia y concatena todos los archivos .md en un único string
    archivos_md = sorted(
        [f for f in input_dir.iterdir() if f.suffix == ".md"],
        key=_sort_key_archivo,
    )

    if not archivos_md:
        raise FileNotFoundError(f"No se encontraron archivos en: {input_dir}")

    logger.info("Fusionando %d archivos .md...", len(archivos_md))

    fragmentos = []
    mapa_paginas = {}

    for archivo in archivos_md:
        texto_raw = archivo.read_text(encoding="utf-8")

        info_match = RE_INFO_TAG.search(texto_raw)
        origen_texto = info_match.group(1).strip() if info_match else "Origen Desconocido"
        mapa_paginas[archivo.name] = origen_texto

        texto_sin_info = RE_INFO_TAG.sub("", texto_raw)
        texto_limpio = limpiar_cabezales(texto_sin_info)

        if not texto_limpio:
            continue

        marcador = MARCADOR_PAGINA.format(archivo=archivo.name)
        fragmentos.append(f"{marcador}\n{texto_limpio}")

    texto_monolitico = "\n\n".join(fragmentos)
    return texto_monolitico, mapa_paginas


def _intentar_llamaindex(texto_monolitico: str) -> Optional[list[dict]]:
    try:
        from llama_index.core import Document
        from llama_index.core.node_parser import MarkdownNodeParser

        doc = Document(
            text=texto_monolitico,
            metadata={"fuente": "documento_monolitico_fusionado"},
        )
        parser = MarkdownNodeParser()
        nodos = parser.get_nodes_from_documents([doc])

        resultados = []
        for nodo in nodos:
            texto_nodo = nodo.text.strip()
            if texto_nodo:
                resultados.append({
                    "texto": texto_nodo,
                    "metadatos_parser": nodo.metadata,
                })
        return resultados
    except ImportError:
        return None


def _splitter_markdown_nativo(texto_monolitico: str) -> list[dict]:
    """
    splitter Markdown basado en encabezados zero-dependency.

    divide el texto monolítico en chunks semánticos usando los
    encabezados Markdown (#, ##, ###) como puntos de corte. cada chunk hereda la jerarquía completa de headers activos
    """
    # headers que actúan como delimitadores semánticos
    HEADER_LEVELS = [
        ("#", "Header_1"),
        ("##", "Header_2"),
        ("###", "Header_3"),
    ]

    lineas = texto_monolitico.split("\n")
    chunks = []
    buffer_lineas = []
    headers_activos = {}

    def _flush_buffer():
        if not buffer_lineas:
            return
        texto_chunk = "\n".join(buffer_lineas).strip()
        if texto_chunk:
            chunks.append({
                "texto": texto_chunk,
                "metadatos_parser": dict(headers_activos),
            })
        buffer_lineas.clear()

    for linea in lineas:
        linea_stripped = linea.strip()

        if PATRON_MARCADOR.match(linea_stripped):
            continue

        matched_header = False
        for prefix, key in HEADER_LEVELS:
            if linea_stripped.startswith(prefix + " ") and not linea_stripped.startswith(prefix + "# "):
                _flush_buffer()
                header_text = linea_stripped[len(prefix) + 1:].strip()
                headers_activos[key] = header_text

                level_idx = [h[1] for h in HEADER_LEVELS].index(key)
                for _, sub_key in HEADER_LEVELS[level_idx + 1:]:
                    headers_activos.pop(sub_key, None)

                matched_header = True
                break

        if not matched_header:
            buffer_lineas.append(linea)

    _flush_buffer()
    return chunks


def ejecutar_chunking_semantico(texto_monolitico: str) -> list[dict]:
    nodos = _intentar_llamaindex(texto_monolitico)
    if nodos is None:
        nodos = _splitter_markdown_nativo(texto_monolitico)
    return nodos


def _resolver_paginas_origen(texto_monolitico: str, mapa_paginas: dict[str, str]) -> list[tuple[int, str]]:
    marcadores_posicion = []
    for match in PATRON_MARCADOR.finditer(texto_monolitico):
        nombre_archivo = match.group(1)
        marcadores_posicion.append((match.start(), nombre_archivo))
    return marcadores_posicion


def enriquecer_nodos_con_origen(
    nodos: list[dict],
    texto_monolitico: str,
    mapa_paginas: dict[str, str],
) -> list[dict]:
    marcadores = _resolver_paginas_origen(texto_monolitico, mapa_paginas)
    texto_limpio_busqueda = PATRON_MARCADOR.sub("", texto_monolitico)

    for nodo in nodos:
        texto_nodo = nodo["texto"]
        pos = texto_monolitico.find(texto_nodo[:100])

        if pos == -1:
            pos_limpio = texto_limpio_busqueda.find(texto_nodo[:100])
            paginas_contribuyentes = _encontrar_paginas_por_posicion(
                pos_limpio, len(texto_nodo), marcadores, texto_monolitico
            )
        else:
            paginas_contribuyentes = _encontrar_paginas_por_posicion(
                pos, len(texto_nodo), marcadores, texto_monolitico
            )

        origenes = []
        for archivo in paginas_contribuyentes:
            info = mapa_paginas.get(archivo, "Origen Desconocido")
            origenes.append({
                "archivo": archivo,
                "descripcion": info,
            })
        nodo["paginas_origen"] = origenes

    return nodos


def _encontrar_paginas_por_posicion(
    pos_inicio: int,
    longitud: int,
    marcadores: list[tuple[int, str]],
    texto: str,
) -> list[str]:
    if pos_inicio == -1:
        return ["desconocido"]

    pos_fin = pos_inicio + longitud
    paginas = []

    for i, (pos_marcador, archivo) in enumerate(marcadores):
        inicio_rango = pos_marcador
        fin_rango = (
            marcadores[i + 1][0] if i + 1 < len(marcadores)
            else len(texto)
        )

        if inicio_rango < pos_fin and fin_rango > pos_inicio:
            if archivo not in paginas:
                paginas.append(archivo)

    return paginas if paginas else ["desconocido"]


def exportar_nodos_auditados(nodos: list[dict], output_file: Path) -> list[dict]:
    nodos_export = []
    for i, nodo in enumerate(nodos, start=1):
        texto = nodo["texto"].strip()
        if not texto:
            continue

        nodos_export.append({
            "nodo_id": i,
            "longitud_caracteres": len(texto),
            "jerarquia_headers": nodo.get("metadatos_parser", {}),
            "paginas_origen": nodo.get("paginas_origen", []),
            "texto": texto,
        })

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(nodos_export, f, ensure_ascii=False, indent=4)

    return nodos_export


def verificar_fusion_pasantia(nodos_export: list[dict]) -> bool:
    frag_10 = "empleo a tiempo parcial paralelo a"
    frag_11 = "los estudios, u otras actividades laborales"

    fusion_exitosa = False
    for nodo in nodos_export:
        texto = nodo["texto"]
        if frag_10 in texto and frag_11 in texto:
            fusion_exitosa = True
            print(f"[OK] Fusión exitosa en nodo #{nodo['nodo_id']}")
            break

    assert fusion_exitosa, "Error: El párrafo de pasantía laboral no fue correctamente fusionado"
    return True


def imprimir_estadisticas(nodos_export: list[dict]) -> None:
    if not nodos_export:
        return

    longitudes = [n["longitud_caracteres"] for n in nodos_export]
    total = len(longitudes)
    promedio = sum(longitudes) / total
    minimo = min(longitudes)
    maximo = max(longitudes)
    mediana = sorted(longitudes)[total // 2]

    print(f"\n{'=' * 72}")
    print("  ESTADÍSTICAS DEL CHUNKING SEMÁNTICO")
    print("=" * 72)
    print(f"  Total de nodos:             {total}")
    print(f"  Longitud promedio:          {promedio:.0f} caracteres")
    print(f"  Longitud mediana:           {mediana} caracteres")
    print(f"  Nodo más corto:             {minimo} caracteres")
    print(f"  Nodo más largo:             {maximo} caracteres")

    # Distribución por rangos
    rangos = {
        "< 200 chars":   sum(1 for l in longitudes if l < 200),
        "200-500":       sum(1 for l in longitudes if 200 <= l < 500),
        "500-1000":      sum(1 for l in longitudes if 500 <= l < 1000),
        "1000-2000":     sum(1 for l in longitudes if 1000 <= l < 2000),
        "2000-5000":     sum(1 for l in longitudes if 2000 <= l < 5000),
        "> 5000 chars":  sum(1 for l in longitudes if l >= 5000),
    }
    print(f"\n  Distribución por tamaño:")
    for rango, count in rangos.items():
        barra = "█" * (count * 40 // total) if total > 0 else ""
        print(f"    {rango:>15s}: {count:>4d}  {barra}")

    print("=" * 72)



def procesar_chunking_merge_then_split() -> None:
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_dir = base_dir / "data" / "processed" / "paginas_normalizadas_v2"
    output_file = base_dir / "data" / "processed" / "nodos_auditados.json"

    
    logger.info("Input:  %s", input_dir)
    logger.info("Output: %s", output_file)
    print("Iniciando chunking...")
    texto_monolitico, mapa_paginas = fusionar_documento_monolitico(input_dir)
    nodos = ejecutar_chunking_semantico(texto_monolitico)
    nodos = enriquecer_nodos_con_origen(nodos, texto_monolitico, mapa_paginas)
    nodos_export = exportar_nodos_auditados(nodos, output_file)

    imprimir_estadisticas(nodos_export)
    verificar_fusion_pasantia(nodos_export)
    print(f"Completado. Resultado en: {output_file}")
 

if __name__ == "__main__":
    procesar_chunking_merge_then_split()