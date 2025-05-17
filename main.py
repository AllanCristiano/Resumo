import os
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

# Configuração do TESSDATA_PREFIX (localiza onde estão os arquivos .traineddata do Tesseract)
for cand in [
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/share/tesseract-ocr/tessdata",
    "/usr/share/tesseract-ocr/tessdata"
]:
    if os.path.isdir(cand):
        os.environ["TESSDATA_PREFIX"] = cand
        break


# Função para listar arquivos PDF em um diretório (busca recursiva)
def listar_arquivos_pdf(diretorio):
    pdf_files = []
    for raiz, _, arquivos in os.walk(diretorio):
        for nome in arquivos:
            if nome.lower().endswith(".pdf"):
                caminho_completo = os.path.join(raiz, nome)
                pdf_files.append(caminho_completo)
    return pdf_files


# Função para converter o PDF em imagens e extrair o texto via OCR
def extract_texts_from_files(pdf_files, lang='por', dpi=300, temp_folder="pages"):
    os.makedirs(temp_folder, exist_ok=True)
    results = []

    for pdf_path in pdf_files:
        print(f"Processando: {pdf_path}")
        all_text = []
        pages = convert_from_path(pdf_path, dpi=dpi, fmt='jpeg', output_folder=temp_folder, paths_only=True)
        for idx, img_path in enumerate(pages, start=1):
            txt = pytesseract.image_to_string(Image.open(img_path), lang=lang)
            all_text.append(f"--- Página {idx} ---\n{txt}")
            print(f"[OK] {os.path.basename(pdf_path)} - página {idx} processada")
        full_text = "\n".join(all_text)
        results.append({'filename': pdf_path, 'text': full_text})

    print(f"\n✅ OCR completo — processados {len(results)} arquivos")
    return results


# Função para extrair informações relevantes usando expressões regulares
def extrair_informacoes(texto):
    # Captura todo o conteúdo até a quebra de linha após "PORTARIA N°"
    padrao_portaria = r"PORTARIA\s+N\.?[º°]\s*([^\r\n]+)"
    # Captura datas no formato "De 26 de janeiro de 2024" ou "26 de janeiro de 2024"
    padrao_data = r"(?:De\s+)?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})"

    match_portaria = re.search(padrao_portaria, texto, flags=re.IGNORECASE)
    numero_portaria = match_portaria.group(1).strip() if match_portaria else None

    match_data = re.search(padrao_data, texto, flags=re.IGNORECASE)
    data_portaria = match_data.group(1).strip() if match_data else None

    texto_depois_data = ""
    if match_data:
        posicao_final_data = match_data.end()
        texto_depois_data = texto[posicao_final_data:].strip()
        pos_primeiro_ponto = texto_depois_data.find('.')
        if pos_primeiro_ponto != -1:
            texto_depois_data = texto_depois_data[:pos_primeiro_ponto + 1].strip()

    return numero_portaria, data_portaria, texto_depois_data


# Função para salvar os resultados em um arquivo .txt
def salvar_resultados_em_txt(ocr_results, arquivo_saida="resultado_ocr.txt"):
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        for ocr_result in ocr_results:
            f.write("=" * 50 + "\n")
            f.write(f"Arquivo: {ocr_result['filename']}\n")
            f.write(f"Número da Portaria: {ocr_result.get('numero_portaria', 'N/A')}\n")
            f.write(f"Data da Portaria: {ocr_result.get('data_portaria', 'N/A')}\n")
            f.write("\n")
            f.write(ocr_result['texto'] + "\n\n")

    print(f"\n✅ Dados salvos em '{arquivo_saida}'")


if __name__ == "__main__":
    # Defina o caminho da pasta onde os PDFs estão armazenados
    pasta = "/home/allan/Documentos/PDFs"
    pdf_arquivos = listar_arquivos_pdf(pasta)
    ocr_results = extract_texts_from_files(pdf_arquivos)

    # Dicionários para tratar portarias duplicadas
    portarias_existentes = {}
    portarias_indices = {}

    # Extração de informações de cada OCR
    for idx, ocr_result in enumerate(ocr_results):
        numero_portaria, data_portaria, texto_depois_data = extrair_informacoes(ocr_result['text'])

        if numero_portaria in portarias_existentes:
            count = portarias_existentes[numero_portaria] + 1
            portarias_existentes[numero_portaria] = count

            if count == 2:
                # Primeira duplicata: atualiza a ocorrência original para ter o sufixo "-1"
                idx_primeira = portarias_indices[numero_portaria]
                ocr_results[idx_primeira]['numero_portaria'] = f"{numero_portaria}-1"

            # Atualiza para a ocorrência atual
            numero_portaria = f"{numero_portaria}-{count}"
        else:
            portarias_existentes[numero_portaria] = 1
            portarias_indices[numero_portaria] = idx

        ocr_result['numero_portaria'] = numero_portaria
        ocr_result['data_portaria'] = data_portaria
        ocr_result['texto'] = texto_depois_data

    # Ordena os resultados em ordem crescente com base no número da portaria
    ocr_results_ordenados = sorted(ocr_results, key=lambda x: x.get('numero_portaria') or "")

    # Salva os resultados ordenados em um arquivo .txt
    salvar_resultados_em_txt(ocr_results_ordenados)
