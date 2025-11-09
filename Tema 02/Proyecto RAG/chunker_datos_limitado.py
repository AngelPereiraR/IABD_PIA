import os
import re
import json
from pathlib import Path
import uuid

# --- CONFIGURACIÓN DE LA ESTRATEGIA ---
INPUT_DIR = Path("documentos_tea_andalucia_limpio")
OUTPUT_FILE = "chunks_tea_andalucia_limited.jsonl" # Nombre diferente para no sobreescribir el completo

# Tamaño objetivo y solapamiento
CHUNK_SIZE = 1500  # Caracteres objetivo por chunk
CHUNK_OVERLAP = 200 # Caracteres de solapamiento

# Límite de archivos para esta versión de prueba
MAX_FILES_TO_PROCESS = 5

class DocumentChunker:
    """
    Divide documentos en chunks semánticos con solapamiento mejorado.
    """
    def __init__(self, chunk_size=1500, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def semantic_chunking(self, text):
        """
        Divide el texto intentando respetar la estructura semántica y aplicando solapamiento inteligente.
        """
        # Lista de separadores por prioridad
        separators = ["\n\n", "\n", ". ", " ", ""]
        
        chunks_to_process = [text]
        
        for separator in separators:
            new_chunks = []
            for chunk in chunks_to_process:
                if len(chunk) > self.chunk_size:
                    splits = chunk.split(separator)
                    current_chunk = ""
                    for split in splits:
                        sep_to_add = separator if separator != "" else ""
                        if len(current_chunk) + len(split) + len(sep_to_add) <= self.chunk_size:
                            current_chunk += split + sep_to_add
                        else:
                            if current_chunk:
                                new_chunks.append(current_chunk.strip())
                                
                            overlap_text = ""
                            if len(current_chunk) > self.chunk_overlap:
                                potential_overlap = current_chunk[-int(self.chunk_overlap * 1.5):]
                                space_index = potential_overlap.find(" ")
                                if space_index != -1 and space_index < len(potential_overlap) - self.chunk_overlap / 2:
                                     overlap_text = potential_overlap[space_index+1:]
                                else:
                                    overlap_text = current_chunk[-self.chunk_overlap:]
                            
                            current_chunk = overlap_text + split + sep_to_add
                    if current_chunk:
                        new_chunks.append(current_chunk.strip())
                else:
                    new_chunks.append(chunk)
            chunks_to_process = new_chunks
            if all(len(c) <= self.chunk_size + 100 for c in chunks_to_process):
                break
        return chunks_to_process

    def extract_metadata_from_text(self, text):
        """
        Intenta extraer metadatos del encabezado del texto limpio.
        """
        metadata = {}
        lines = text.split('\n')
        for line in lines[:25]:
            if line.startswith("TÍTULO:"):
                metadata['title'] = line.replace("TÍTULO:", "").strip()
            elif line.startswith("URL ORIGINAL:"):
                metadata['original_url'] = line.replace("URL ORIGINAL:", "").strip()
            elif line.startswith("TIPO:"):
                metadata['type'] = line.replace("TIPO:", "").strip()
        return metadata

def process_directory_limited(input_dir, output_file, max_files):
    chunker = DocumentChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    total_chunks = 0
    processed_files = 0
    
    print(f"Iniciando proceso LIMITADO de chunking desde: {input_dir}")
    print(f"Se procesarán máximo {max_files} archivos.")
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if processed_files >= max_files: break

                if file.endswith(".txt") and not file.startswith("00_"):
                    file_path = Path(root) / file
                    processed_files += 1
                    category = Path(root).name
                    if category == input_dir.name: category = "general"

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            full_text = f.read()
                        doc_metadata = chunker.extract_metadata_from_text(full_text)
                        content_start_marker = "CONTENIDO:"
                        if content_start_marker in full_text:
                            parts = full_text.split(content_start_marker, 1)
                            text_to_chunk = re.sub(r'^=+\n+', '', parts[1].lstrip()).strip() if len(parts) > 1 else full_text
                        else:
                            text_to_chunk = full_text

                        chunks = chunker.semantic_chunking(text_to_chunk)
                        for i, chunk_text in enumerate(chunks):
                            if len(chunk_text) < 50: continue
                            chunk_data = {
                                "id": str(uuid.uuid4()),
                                "text": chunk_text,
                                "metadata": {
                                    "source_file": file,
                                    "category": category,
                                    "chunk_index": i,
                                    "total_chunks_in_doc": len(chunks),
                                    **doc_metadata
                                }
                            }
                            out_f.write(json.dumps(chunk_data, ensure_ascii=False) + '\n')
                            total_chunks += 1
                        print(f"Procesado ({processed_files}/{max_files}): {file}")
                    except Exception as e:
                        print(f"Error procesando {file}: {e}")
            if processed_files >= max_files: break

    print(f"\n--- Proceso LIMITADO finalizado ---")
    print(f"Documentos procesados: {processed_files}")
    print(f"Total chunks generados: {total_chunks}")
    print(f"Archivo de salida: {output_file}")

if __name__ == "__main__":
    if not INPUT_DIR.exists():
        print(f"ERROR: No se encuentra el directorio de entrada: {INPUT_DIR}")
    else:
        process_directory_limited(INPUT_DIR, OUTPUT_FILE, MAX_FILES_TO_PROCESS)