import os
import re
import nltk
from nltk.tokenize import word_tokenize
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

# Certifica-se de que os recursos necessários do NLTK estão disponíveis
nltk.download('punkt')
nltk.download('stopwords')

# Configuração do TESSDATA_PREFIX
for cand in [
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/share/tesseract-ocr/tessdata",
    "/usr/share/tesseract-ocr/tessdata"
]:
    if os.path.isdir(cand):
        os.environ["TESSDATA_PREFIX"] = cand
        break

# Função para listar arquivos PDF em um diretório
def listar_arquivos_pdf(diretorio):
    pdf_files = []
    for raiz, _, arquivos in os.walk(diretorio):
        for nome in arquivos:
            if nome.lower().endswith(".pdf"):
                caminho_completo = os.path.join(raiz, nome)
                pdf_files.append(caminho_completo)
    return pdf_files

# Função para converter PDF em imagens e extrair texto via OCR
def extract_texts_from_files(pdf_files, lang='por', dpi=600, temp_folder="pages"):
    os.makedirs(temp_folder, exist_ok=True)
    results = []
    for idx, pdf_path in enumerate(pdf_files, start=1):
        print(f"{idx}/{len(pdf_files)} - Processando: {pdf_path}")
        all_text = []
        pages = convert_from_path(pdf_path, dpi=dpi, fmt='jpeg', output_folder=temp_folder, paths_only=True)
        for i, img_path in enumerate(pages, start=1):
            txt = pytesseract.image_to_string(Image.open(img_path), lang=lang)
            all_text.append(f"--- Página {i} ---\n{txt}")
            print(f"[OK] {os.path.basename(pdf_path)} - página {i} processada")
        full_text = "\n".join(all_text)
        results.append({'filename': pdf_path, 'text': full_text})
    print(f"\n✅ OCR completo — processados {len(results)} arquivos")
    return results

# Função para formatar a data no padrão YYYY-MM-DD
def formatar_data(data_portaria):
    meses = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
        "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
        "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
    }
    
    if not data_portaria:
        return "0000-00-00"

    match = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", data_portaria, flags=re.IGNORECASE)
    if match:
        dia, mes_texto, ano = match.groups()
        mes = meses.get(mes_texto.lower(), "00")
        return f"{ano}-{mes}-{dia.zfill(2)}"
    
    return "0000-00-00"

# Função para extrair informações e capturar as 20 primeiras palavras após a data
def extrair_informacoes(texto):
    padrao_portaria = r"PORTARIA\s+N\.?[º°]\s*([^\r\n]+)"
    match_portaria = re.search(padrao_portaria, texto, flags=re.IGNORECASE)
    numero_portaria = match_portaria.group(1).strip() if match_portaria else None

    padrao_data = r"(?:De\s+)?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})"
    match_data = re.search(padrao_data, texto, flags=re.IGNORECASE)
    data_portaria = match_data.group(1).strip() if match_data else None

    trecho_capturado = "Resumo não disponível"
    if match_data:
        posicao_final_data = match_data.end()
        resto_texto = texto[posicao_final_data:].strip()
        palavras = word_tokenize(resto_texto, language='portuguese')
        if palavras:
            trecho_capturado = " ".join(palavras[:20])  # Captura as 20 primeiras palavras após a data

    # Verificação para evitar erro
    data_formatada = formatar_data(data_portaria) if data_portaria else "0000-00-00"

    return numero_portaria, data_formatada, trecho_capturado

# Função para renomear os arquivos PDF
def renomear_arquivo(original_path, numero_portaria, data_portaria):
    if numero_portaria and data_portaria != "0000-00-00":
        # Remove caracteres inválidos do número da portaria
        numero_portaria = re.sub(r'[^0-9A-Za-z]', '', numero_portaria)
        novo_nome = f"{numero_portaria}-{data_portaria}.pdf"
        novo_caminho = os.path.join(os.path.dirname(original_path), novo_nome)
        if os.path.exists(original_path):
            try:
                os.rename(original_path, novo_caminho)
                print(f"✅ Arquivo renomeado: {os.path.basename(original_path)} → {novo_nome}")
                return novo_caminho
            except Exception as e:
                print(f"⚠️ Erro ao renomear arquivo {original_path}: {e}")
        else:
            print(f"⚠️ Arquivo não encontrado: {original_path}")
    return original_path

# Função para salvar os resultados em TXT
def salvar_resultados_em_txt(ocr_results, arquivo_saida):
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        for result in ocr_results:
            f.write("=" * 50 + "\n")
            f.write(f"Arquivo: {result['filename']}\n")
            f.write(f"Número documento: {result.get('numero_portaria', 'N/A')}\n")
            f.write(f"Data: {result.get('data_portaria', '0000-00-00')}\n")
            f.write(f"Trecho capturado: {result.get('trecho_capturado', 'Resumo não disponível')}\n")
            f.write("\n")
    print(f"\n✅ Dados salvos em '{arquivo_saida}'.")

# Função para criar uma nova pasta e mover os arquivos renomeados para ela
def mover_arquivos_para_pasta(arquivos, destino):
    os.makedirs(destino, exist_ok=True)  # Cria a pasta se não existir
    for arquivo in arquivos:
        caminho_atual = arquivo['filename']
        novo_caminho = os.path.join(destino, os.path.basename(caminho_atual))
        try:
            os.rename(caminho_atual, novo_caminho)
            print(f"✅ Arquivo movido: {os.path.basename(caminho_atual)} → {novo_caminho}")
            # Atualiza o caminho do arquivo no dicionário
            arquivo['filename'] = novo_caminho
        except Exception as e:
            print(f"⚠️ Erro ao mover arquivo {caminho_atual}: {e}")

if __name__ == "__main__":
    # Diretório de origem contendo os PDFs
    diretorio_origem = "/home/allan/Documentos/arquivos/Leis Complementares"
    # Diretório de destino para os arquivos renomeados
    pasta_destino = "/home/allan/Documentos/arquivos/leis_complementares_renomeadas"
    
    pdf_arquivos = listar_arquivos_pdf(diretorio_origem)
    ocr_results = extract_texts_from_files(pdf_arquivos)

    ocr_results_valid = []
    ocr_results_missing = []

    for ocr_result in ocr_results:
        numero_portaria, data_formatada, trecho_capturado = extrair_informacoes(ocr_result['text'])
        # Verifica se a data extraída está dentro do intervalo desejado (2022 a 2025)
        ano_extraido = int(data_formatada.split("-")[0]) if data_formatada != "0000-00-00" else 0
        if not numero_portaria or data_formatada == "0000-00-00" or not (2022 <= ano_extraido <= 2025):
            ocr_result.update({'numero_portaria': numero_portaria or "N/A",
                               'data_portaria': data_formatada,
                               'trecho_capturado': trecho_capturado})
            ocr_results_missing.append(ocr_result)
        else:
            novo_caminho = renomear_arquivo(ocr_result['filename'], numero_portaria, data_formatada)
            ocr_result.update({'filename': novo_caminho,
                               'numero_portaria': numero_portaria, 
                               'data_portaria': data_formatada,
                               'trecho_capturado': trecho_capturado})
            ocr_results_valid.append(ocr_result)

    salvar_resultados_em_txt(ocr_results_valid, "resultado_ocr.txt")
    salvar_resultados_em_txt(ocr_results_missing, "resultado_ocr_missing.txt")

    # Cria a pasta de destino e move os arquivos renomeados
    mover_arquivos_para_pasta(ocr_results_valid, pasta_destino)

    print("\n✅ Processamento concluído!")
