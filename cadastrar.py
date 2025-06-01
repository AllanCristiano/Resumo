import requests
import re

def post_documento(documento):
    url = "http://localhost:3001/documento"  # Substitua pela URL desejada
    dados = {
        "type": "PORTARIA",
        "number": f"{documento[0]}",
        "title": f"PORTARIA Nº {documento[0]}",
        "description": f"{documento[2]}",
        "date": f"{documento[1][0]}-{documento[1][1]}-{documento[1][2]}",
        "url": ""
    }  # Substitua pelos dados que deseja enviar

    response = requests.post(url, json=dados)

    # Exibir a resposta
    print(f"Status Code: {response.status_code}")
    print(f"Resposta: {response.text}")


def extrair_elementos(arquivo):
    # Abre e lê o conteúdo do arquivo
    with open(arquivo, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Divide o conteúdo usando linhas delimitadoras (linhas compostas por "=")
    blocos = re.split(r'\n=+\n', conteudo)

    elementos = []
    # Para cada bloco, extrai as informações desejadas
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue

        # Procura pelo número do documento, data e trecho capturado
        match_numero = re.search(r'Número documento:\s*(.+)', bloco)
        match_data   = re.search(r'Data:\s*(\d{4}-\d{2}-\d{2})', bloco)
        match_trecho = re.search(r'Trecho capturado:\s*(.+)', bloco)

        if match_numero and match_data and match_trecho:
            numero_doc = match_numero.group(1).strip()
            data_str = match_data.group(1).strip()
            trecho = match_trecho.group(1).strip()

            # Separa a data em ano, mês e dia
            ano, mes, dia = data_str.split('-')
            # Converte o dia para inteiro e depois para string para remover o zero à esquerda
            dia = str(int(dia))
            
            # Adiciona o elemento na lista: [número do documento, (ano, mes, dia), trecho capturado]
            elementos.append([numero_doc, (ano, mes, dia), trecho])

    return elementos


if __name__ == "__main__":
    arquivo = "resultado_ocr.txt"  
    lista_elementos = extrair_elementos(arquivo)
    for item in lista_elementos:
        post_documento(item)


