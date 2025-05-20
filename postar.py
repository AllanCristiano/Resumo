from playwright.sync_api import sync_playwright
import re

# Mapeamento dos meses em português para seus respectivos valores numéricos.
MONTH_MAP = {
    'janeiro': 1,
    'fevereiro': 2,
    'março': 3,
    'abril': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'outubro': 10,
    'novembro': 11,
    'dezembro': 12
}

def postar(item):
    try:
        with sync_playwright() as p:
            # Abre o navegador em modo não headless para visualização
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Acessa a página de login
            page.goto("https://transparencia.aracaju.se.gov.br/prefeitura/wp-admin")
            # Aguarda até que o botão de login esteja visível
            page.wait_for_selector("#wp-submit", state="visible", timeout=10000)
            
            # Preenche os dados de login
            page.fill("#user_login", "usuario")
            page.fill("#user_pass", "senha")
            page.click("#wp-submit")
            
            # Aguarda até que o menu "Documents" esteja visível e clica nele
            selector_documents = "a[href='edit.php?post_type=dlp_document']"
            page.wait_for_selector(selector_documents, state="visible", timeout=10000)
            page.click(selector_documents)
            
            # aguarda um pouco para garantir que o DOM seja atualizado
            page.wait_for_timeout(2000)
            
            page.wait_for_selector("text=Add New", state="visible", timeout=40000)
            page.click("text=Add New")

            page.wait_for_selector("text=Add New Document", state="visible", timeout=10000)
            page.fill("#title", f"Portaria nº {item[1]}")

            # FrameLocator para o iframe do TinyMCE
            frame = page.frame_locator('#content_ifr')

            # Preenche texto simples
            frame.locator('body').fill(f"{item[3]}")

            # Preenche campo categoria
            page.check('#in-doc_categories-185')

            # Editar o campo de data
            page.click('div.misc-pub-curtime a.edit-timestamp')
            page.wait_for_selector('#timestampdiv', state='visible')

            # Preencha os campos de data/hora:
            page.fill('input#jj', f'{item[2][0]}')              # Dia: 20
            page.select_option('select#mm', f'{int(item[2][1]):02d}')    # Mês: maio (value="05")
            page.fill('input#aa', f'{item[2][2]}')            # Ano: 2024
            page.fill('input#hh', '14')              # Hora: 14h
            page.fill('input#mn', '30')              # Minuto: 30

            page.click("#timestampdiv > p > a.save-timestamp.hide-if-no-js.button")

            # upload do arquivo
            # Seleciona a opção de upload
            page.select_option('#dlw_document_link_type', 'file')
            page.wait_for_selector("#dlw_add_file_button", state="visible")
            page.click("#dlw_add_file_button")
            # Aguarda o seletor do input de upload ficar visível
            page.wait_for_selector("#media-search-input", state="visible")
            # Preenche o campo de upload
            nome_arquivo = item[1].replace("/", "") + ".pdf"
            # pesquisar o arquivo
            page.fill("#media-search-input", f"{nome_arquivo}")

            # aguarda um pouco para garantir que o DOM seja atualizado
            page.wait_for_timeout(16000)
            # Aguarda o arquivo aparecer na lista de resultados        
            page.wait_for_selector(f'ul#__attachments-view-48 li:has-text("{nome_arquivo}")', state="visible", timeout=20000)
            # seleciona o arquivo
            page.click(f'ul#__attachments-view-48 li:has-text("{nome_arquivo}")')

            # Aguarda o botão de "Adicionar" ficar visível e clica nele
            page.wait_for_selector("#__wp-uploader-id-0 > div.media-frame-toolbar > div > div.media-toolbar-primary.search-form > button", state="visible", timeout=20000)
            page.click("#__wp-uploader-id-0 > div.media-frame-toolbar > div > div.media-toolbar-primary.search-form > button")
            
            page.click("#publish")
            page.wait_for_selector("text=Post publicado.", state="visible", timeout=40000)
        
            # Mantém o navegador aberto para análise
            # input("Pressione ENTER para fechar o navegador...")
            browser.close()
    except Exception as e:
        escrever_log(f"Portaria {item[2]} erro na postagem.", "erros.txt")
        errados.append(item[2])
        run()

def parse_portarias(file_path):
    """
    Lê um arquivo de texto estruturado contendo registros de portarias,
    extrai os campos 'Arquivo', 'Número da Portaria', 'Data da Portaria'
    (convertendo o mês para o valor numérico) e o restante do texto.
    
    Retorna uma lista de tuplas no formato:
      (arquivo, número_portaria, (dia, mês, ano), texto)
      
    :param file_path: Caminho para o arquivo TXT.
    :return: Lista de tuplas com os dados extraídos.
    """
    result_list = []
    
    # Lê o conteúdo do arquivo (garanta que a codificação esteja correta)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Divide o conteúdo usando o delimitador de linhas (várias "=")
    records = re.split(r"={3,}", content)
    records = [record.strip() for record in records if record.strip()]
    
    for rec in records:
        # Extração do campo "Arquivo:"
        arquivo_match = re.search(r"Arquivo:\s*(.+)", rec)
        arquivo = arquivo_match.group(1).strip() if arquivo_match else ""
        
        # Extração do campo "Número da Portaria:"
        numero_match = re.search(r"[Nn]úmero da Portaria:\s*(.+)", rec)
        numero = numero_match.group(1).strip() if numero_match else ""
        
        # Extração do campo "Data da Portaria:"
        # Padrão: [dia] de [mês] de [ano]
        data_match = re.search(r"Data da Portaria:\s*(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})", rec, re.IGNORECASE)
        if data_match:
            dia = int(data_match.group(1))
            mes_str = data_match.group(2).lower()
            mes = MONTH_MAP.get(mes_str, None)
            ano = int(data_match.group(3))
            data_portaria = (dia, mes, ano)
        else:
            data_portaria = None
        
        # Extração do "texto": junta todas as linhas que não sejam cabeçalhos
        lines = rec.splitlines()
        text_lines = []
        for line in lines:
            if line.startswith("Arquivo:") or line.startswith("Número da Portaria:") or line.startswith("Data da Portaria:"):
                continue
            text_lines.append(line.strip())
        texto = " ".join(text_lines).strip()
        
        result_list.append((arquivo, numero, data_portaria, texto))
    
    return result_list

postados = []
errados = []

def escrever_log(mensagem, arquivo):
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(mensagem + "\n")

def run():
    file_path = 'resultado_ocr_atualizado.txt'
    portarias = parse_portarias(file_path)
    
    for item in portarias:
        if item[2] in postados:
            continue
        if item[2] in errados:
            continue
        postar(item)
        postados.append(item[2])
        escrever_log(f"Portaria {item[2]} postada com sucesso.", "acertos.txt")
    
    for item in errados:
        if item[2] in postados:
            continue        
        postar(item)
        postados.append(item[2])
        escrever_log(f"Portaria {item[2]} postada com sucesso apos erros.", "acertos.txt")

if __name__ == "__main__":
    run()

