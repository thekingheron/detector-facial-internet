import time
import requests
import argparse
import os
from ftplib import FTP



TESTING_MODE = True
APITOKEN = 'uvy/sDZy70uNXUtoWUVHGItTNSXARmI1OaA0TFOsh3a6hMtkmVi4gNQroJzpt+0HQI0pn7dZbso=' # Your API Token

parser = argparse.ArgumentParser()
parser.add_argument('--id', help='ID do usuário')
args = parser.parse_args()
id_usuario = args.id
#usuario = 1533706535
#id_usuario = str(usuario)

def search_by_face(image_file):
    if TESTING_MODE:
        print('****** TESTING MODE search, results are inaccurate, and queue wait is long, but credits are NOT deducted ******')

    site='https://facecheck.id'
    headers = {'accept': 'application/json', 'Authorization': APITOKEN}
    files = {'images': open(image_file, 'rb'), 'id_search': None}
    response = requests.post(site+'/api/upload_pic', headers=headers, files=files).json()

    if response['error']:
        return f"{response['error']} ({response['code']})", None

    id_search = response['id_search']
    print(response['message'] + ' id_search='+id_search)
    json_data = {'id_search': id_search, 'with_progress': True, 'status_only': False, 'demo': TESTING_MODE}

    while True:
        response = requests.post(site+'/api/search', headers=headers, json=json_data).json()
        if response['error']:
            return f"{response['error']} ({response['code']})", None
        if response['output']:
            return None, response['output']['items']
        print(f'{response["message"]} progress: {response["progress"]}%')
        time.sleep(1)

def search_and_print_results():
    time.sleep(5)
    caminho_imagem = os.path.join(id_usuario, 'imagem.jpg')
    image_file = caminho_imagem 
    caminho_resultado = os.path.join(id_usuario, f'{id_usuario}.html')

    # Pesquisar na Internet por rosto
    error, urls_images = search_by_face(image_file)

    if urls_images:
        # Inicializar a string HTML com a estrutura básica do documento
        html = '''
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                }
                .gallery {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 20px;
                }
                .result {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    width: 300px;
                    border: 1px solid #ccc;
                    padding: 10px;
                    border-radius: 5px;
                }
                .result img {
                    width: 200px;
                    height: auto;
                    margin-bottom: 10px;
                }
                .details {
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="gallery">
        '''

        for im in urls_images:
            score = im['score']
            url = im['url']
            image_base64 = im['base64']

            # Adicionar o layout HTML para exibir as informações da imagem
            html += f'''
            <div class="result">
                <a href="{url}" target="_blank">
                    <img src="{image_base64}" alt="Imagem encontrada">
                </a>
                <div class="details">
                    <h3>Site:</h3>
                    <p>{url}</p>
                    <h3>Pontos:</h3>
                    <p>{score}</p>
                </div>
            </div>
            '''

        # Fechar a estrutura do documento HTML
        html += '''
            </div>
        </body>
        </html>
        '''

        # Salvar o HTML como um arquivo
        with open(caminho_resultado, 'w', encoding='utf-8') as file:
            file.write(html)

        # Upload do arquivo para o servidor FTP
        ftp_host = 's1.serv00.com'
        ftp_user = 'f8969_facecheck2'
        ftp_password = 'Heron!23'
        ftp_directory = ''

        with FTP(ftp_host) as ftp:
            ftp.login(ftp_user, ftp_password)
            ftp.cwd(ftp_directory)
            
            with open(caminho_resultado, 'rb') as file:
                ftp.storbinary(f'STOR {os.path.basename(caminho_resultado)}', file)

        print(f"Arquivo 'resultado.html' salvo com sucesso no servidor FTP!")
    else:
        print("Nenhum link de imagem encontrado.")

# Verificar se o módulo está sendo executado diretamente
if __name__ == "__main__":
    search_and_print_results()