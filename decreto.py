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
        # Converte cada PDF em imagens
        pages = convert_from_path(pdf_path, dpi=dpi, fmt='jpeg', output_folder=temp_folder, paths_only=True)
        for i, img_path in enumerate(pages, start=1):
            txt = pytesseract.image_to_string(Image.open(img_path), lang=lang)
            all_text.append(f"--- Página {i} ---\n{txt}")
            print(f"[OK] {os.path.basename(pdf_path)} - página {i}/{len(pages)} processada")
        full_text = "\n".join(all_text)
        results.append({'filename': pdf_path, 'text': full_text})
    print(f"\n✅ OCR completo — processados {len(results)} arquivos")
    return results

# Função para formatar a data no padrão YYYY-MM-DD
def formatar_data(data_texto):
    meses = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
        "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
        "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
    }
    
    if not data_texto:
        return "0000-00-00"

    # Tenta extrair dia, mês e ano no formato "04 de janeiro de 2022"
    match = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", data_texto, flags=re.IGNORECASE)
    if match:
        dia, mes_texto, ano = match.groups()
        mes = meses.get(mes_texto.lower(), "00")
        return f"{ano}-{mes}-{dia.zfill(2)}"
    return "0000-00-00"

# Função para extrair o número do decreto e a data do cabeçalho
def extrair_informacoes(texto):
    # Padrão para capturar o cabeçalho do decreto.
    # Exemplo esperado: "DECRETO N.º 6.655 DE 04 DE JANEIRO" ou "DECRETO N.º 6.655 DE 04 DE JANEIRO DE 2022"
    padrao_header = r"DECRETO\s+N\.?\s*[º°o]?\s*([\d.,]+)(?:\s*DE\s+(\d{1,2}\s+de\s+\w+(?:\s+de\s+\d{4})?))?"
    match_header = re.search(padrao_header, texto, flags=re.IGNORECASE)

    if match_header:
        numero_decreto = match_header.group(1).strip()
        data_parte = match_header.group(2).strip() if match_header.group(2) else ""
        # Se a parte da data não contém o ano, tenta procurar o padrão "Aracaju, 04 de janeiro de 2022"
        if data_parte and not re.search(r"de\s+\d{4}", data_parte):
            match_fallback = re.search(r"Aracaju,\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", texto, flags=re.IGNORECASE)
            if match_fallback:
                data_parte = match_fallback.group(1).strip()
        data_formatada = formatar_data(data_parte) if data_parte else "0000-00-00"
        posicao = match_header.end()
    else:
        numero_decreto = None
        data_formatada = "0000-00-00"
        posicao = 0

    # Captura as 20 primeiras palavras após o cabeçalho
    resto_texto = texto[posicao:].strip()
    palavras = word_tokenize(resto_texto, language='portuguese')
    trecho_capturado = " ".join(palavras[:20]) if palavras else "Resumo não disponível"

    return numero_decreto, data_formatada, trecho_capturado

# Função para renomear os arquivos PDF usando as informações extraídas
def renomear_arquivo(original_path, numero_decreto, data_formatada):
    if numero_decreto and data_formatada != "0000-00-00":
        # Remove caracteres inválidos do número do decreto
        numero_decreto_limpo = re.sub(r'[^0-9A-Za-z]', '', numero_decreto)
        novo_nome = f"{numero_decreto_limpo}-{data_formatada}.pdf"
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

# Função para salvar os resultados em um arquivo TXT
def salvar_resultados_em_txt(ocr_results, arquivo_saida):
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        for result in ocr_results:
            f.write("=" * 50 + "\n")
            f.write(f"Arquivo: {result['filename']}\n")
            f.write(f"Número do Decreto: {result.get('numero_decreto', 'N/A')}\n")
            f.write(f"Data: {result.get('data_decreto', '0000-00-00')}\n")
            f.write(f"Trecho capturado: {result.get('trecho_capturado', 'Resumo não disponível')}\n")
            f.write("\n")
    print(f"\n✅ Dados salvos em '{arquivo_saida}'.")

# Função para mover os arquivos renomeados para a pasta de destino
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

# Função para processar documentos em blocos
def processar_em_blocos(pdf_files, tamanho_bloco=100):
    total_arquivos = len(pdf_files)
    for inicio in range(0, total_arquivos, tamanho_bloco):
        fim = min(inicio + tamanho_bloco, total_arquivos)
        print(f"\n🔹 Processando bloco {inicio+1} a {fim} de {total_arquivos} arquivos...\n")
        
        # Extrai texto via OCR para os arquivos do bloco
        ocr_results = extract_texts_from_files(pdf_files[inicio:fim])
        ocr_results_valid = []
        ocr_results_missing = []

        for ocr_result in ocr_results:
            numero_decreto, data_formatada, trecho_capturado = extrair_informacoes(ocr_result['text'])
            
            # Validação: verifica se a data contém ano entre 2022 e 2025
            ano_extraido = int(data_formatada.split("-")[0]) if data_formatada != "0000-00-00" else 0
            if not numero_decreto or data_formatada == "0000-00-00" or not (2022 <= ano_extraido <= 2025):
                ocr_result.update({
                    'numero_decreto': numero_decreto or "N/A",
                    'data_decreto': data_formatada,
                    'trecho_capturado': trecho_capturado
                })
                ocr_results_missing.append(ocr_result)
            else:
                novo_caminho = renomear_arquivo(ocr_result['filename'], numero_decreto, data_formatada)
                ocr_result.update({
                    'filename': novo_caminho,
                    'numero_decreto': numero_decreto, 
                    'data_decreto': data_formatada,
                    'trecho_capturado': trecho_capturado
                })
                ocr_results_valid.append(ocr_result)

        # Salva os resultados do bloco em arquivos TXT separados
        salvar_resultados_em_txt(ocr_results_valid, f"resultado_ocr_{inicio+1}-{fim}.txt")
        salvar_resultados_em_txt(ocr_results_missing, f"resultado_ocr_missing_{inicio+1}-{fim}.txt")

        # Move os arquivos renomeados para o diretório de destino
        mover_arquivos_para_pasta(ocr_results_valid, pasta_destino)

        print(f"\n✅ Bloco {inicio+1}-{fim} concluído!\n")

if __name__ == "__main__":
    # Diretório de origem contendo os PDFs (no exemplo, decretos)
    diretorio_origem = "/home/allan/Documentos/arquivos/Decretos"
    # Diretório de destino para os arquivos renomeados
    pasta_destino = "/home/allan/Documentos/arquivos/decretos_renomeados"
    
    pdf_arquivos = listar_arquivos_pdf(diretorio_origem)
    
    # Processa os arquivos em blocos de 100
    processar_em_blocos(pdf_arquivos, tamanho_bloco=100)
    
    print("\n✅ Processamento concluído!")
