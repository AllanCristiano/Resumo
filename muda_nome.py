import os


def atualizar_txt_com_novos_arquivos(arquivo_txt_original, arquivo_txt_atualizado):
    # Lê o conteúdo do arquivo original
    with open(arquivo_txt_original, "r", encoding="utf-8") as file:
        conteudo = file.read()

    # Separa os registros pelos delimitadores (linhas de "=")
    blocos = conteudo.split("==================================================")

    # Preparar duas listas: uma para os registros originais e outra para os atualizados
    registros = []  # cada registro: (arquivo, numero_portaria, data_portaria, texto)
    registros_atualizados = []

    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue
        linhas = bloco.splitlines()
        if len(linhas) < 3:
            continue  # pula blocos sem os cabeçalhos esperados

        # Extrai os campos básicos:
        caminho_pdf = linhas[0].replace("Arquivo:", "").strip()
        numero_portaria = linhas[1].replace("Número da Portaria:", "").strip()
        data_portaria = linhas[2].replace("Data da Portaria:", "").strip()
        texto = "\n".join(linhas[3:]).strip()

        registros.append((caminho_pdf, numero_portaria, data_portaria, texto))

    # Para cada registro, crie um novo nome para o PDF e tente renomeá-lo
    for reg in registros:
        caminho_pdf, numero_portaria, data_portaria, texto = reg

        # Gere o novo nome a partir dos campos. Exemplo: "1002024.pdf"
        novo_num = numero_portaria.replace("/", "")
        novo_nome = f"{novo_num}.pdf"

        # Mantém o mesmo diretório de origem
        diretorio = os.path.dirname(caminho_pdf)
        novo_caminho = os.path.join(diretorio, novo_nome)

        try:
            os.rename(caminho_pdf, novo_caminho)
            print(f"Arquivo '{caminho_pdf}' renomeado para '{novo_caminho}'.")
        except Exception as e:
            print(f"Erro ao renomear '{caminho_pdf}': {e}")
            # Se ocorrer algum erro, mantém o nome original.
            novo_caminho = caminho_pdf

        # Atualiza o registro com o novo caminho do PDF
        registros_atualizados.append((novo_caminho, numero_portaria, data_portaria, texto))

    # Reconstroi o conteúdo do arquivo de texto atualizado
    novo_conteudo = ""
    for reg in registros_atualizados:
        arquivo_atual, num_port, data_port, resto_texto = reg
        novo_conteudo += "==================================================\n"
        novo_conteudo += f"Arquivo: {arquivo_atual}\n"
        novo_conteudo += f"Número da Portaria: {num_port}\n"
        novo_conteudo += f"Data da Portaria: {data_port}\n"
        if resto_texto:
            novo_conteudo += resto_texto + "\n"
    novo_conteudo += "==================================================\n"  # linha de fechamento se desejar

    # Escreve o novo conteúdo em um arquivo (pode ser o mesmo, se quiser sobrescrever)
    with open(arquivo_txt_atualizado, "w", encoding="utf-8") as file:
        file.write(novo_conteudo)

    print(f"Arquivo de texto atualizado salvo em '{arquivo_txt_atualizado}'.")


# Exemplo de uso:
arquivo_original = "resultado_ocr.txt"  # arquivo que contém os dados originais extraídos
arquivo_atualizado = "resultado_ocr_atualizado.txt"  # nome para o arquivo com os nomes atualizados
atualizar_txt_com_novos_arquivos(arquivo_original, arquivo_atualizado)
