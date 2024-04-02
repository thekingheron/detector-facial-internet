from urllib import request
import dlib, time, telebot, sqlite3, shutil, os, subprocess, cv2, threading
from functools import partial

# Configurações do bot
TOKEN = '6671840751:AAHHsQEnXow-eo467qrNv6h7C8qrw_QTOQ4'

# Conexão com o banco de dados SQLite
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Criação da tabela se não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INT,
        name TEXT,
        username TEXT,
        number TEXT,
        email TEXT,
        balance REAL,
        password TEXT,
        photo BLOB,
        folder_name TEXT
    )
''')
conn.commit()

# Criar instância do bot
bot = telebot.TeleBot(TOKEN)
estados_permitir_foto = {}
fila = []
#permitir_foto = False

def enviar_notificacao(user_id, mensagem):
    bot.send_message(user_id, mensagem)


def processar_solicitacao(user_id):
    # Aqui você pode escrever o código para processar a solicitação
    print("Etapa 4 - Processando Solicitação:", user_id)
    # e obter o resultado desejado
    resultado = f"Processando solicitação para o ID do usuário: {user_id}"
    return resultado


@bot.message_handler(commands=['buscar_sosia'])
def buscar_pessoa_command(message):
    # Pegar o ID do usuário que solicitou o comando
    user_id = message.from_user.id
    #global permitir_foto
    estados_permitir_foto[user_id] = True
    folder_name = str(user_id)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    # Copiar o arquivo facecheck.py para a pasta permanente
    #shutil.copy('facecheck.py', os.path.join(folder_name, 'facecheck.py'))
    # Enviar uma resposta ao usuário
    
    bot.reply_to(message, "Envie uma imagem em boa qualidade e iremos buscar imagens suas ou de pessoas parecidas com você ao redor do mundo!")     

def is_fila_vazia():
    return len(fila) == 0
@bot.message_handler(content_types=['photo'])
def upload_image(message):
    # Pegar o ID do usuário que enviou a imagem
    user_id = message.from_user.id

    # Verificar o estado de permitir_foto para o user_id específico
    if not estados_permitir_foto.get(user_id, False):
        # Informar ao usuário que o envio de fotos está restrito
        bot.reply_to(message, "O envio de fotos está restrito. Use o comando /buscar_sosia e você poderá enviar fotos!")
        return

    folder_name = str(user_id)
    image_file = bot.get_file(message.photo[-1].file_id)
    image_path = image_file.file_path
    image_url = f"https://api.telegram.org/file/bot{TOKEN}/{image_path}"
    response = request.urlopen(image_url)
    id_usuario = user_id

    with open(os.path.join(folder_name, 'completa.jpg'), 'wb') as f:
        f.write(response.read())

    # Carregar o classificador de faces do dlib
    detector = dlib.get_frontal_face_detector()

    # Carregar a imagem usando o OpenCV
    image = cv2.imread(os.path.join(folder_name, 'completa.jpg'))

    # Converter para escala de cinza
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detectar rostos na imagem
    faces = detector(gray)

    # Verificar se foi encontrado algum rosto
    if len(faces) > 0:
        # Definir o fator de aumento do tamanho do recorte
        scale_factor = 2.0  # Você pode ajustar esse valor conforme necessário

        # Recortar e salvar apenas o primeiro rosto encontrado
        face = faces[0]
        (x, y, w, h) = (face.left(), face.top(), face.width(), face.height())

        # Aplicar o fator de aumento ao tamanho do recorte
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)

        # Ajustar as coordenadas para garantir que o recorte permaneça dentro dos limites da imagem
        x = max(0, x - (new_w - w) // 2)
        y = max(0, y - (new_h - h) // 2)

        # Recortar a face com as novas coordenadas e dimensões
        cropped_face = image[y:y+new_h, x:x+new_w]

        # Salvar a face recortada
        cv2.imwrite(os.path.join(folder_name, 'imagem.jpg'), cropped_face)

        # Enviar uma resposta ao usuário
        bot.reply_to(message, "O rosto da sua imagem foi reconhecido, iremos fazer a busca por toda internet, isso pode demorar alguns minutos!  Agora iremos te adiicionar em uma fila!")
        time.sleep(5)
        bot.reply_to(message, "Procurando fila...")
        time.sleep(8)
        
        # Lógica adicional após o processamento bem-sucedido
        fila.append(user_id)
        posicao_fila = len(fila)
        bot.send_message(chat_id=message.chat.id, text=f"Fila encontrada! Você está em {posicao_fila}° na fila!")

        tempo_espera = 360 * posicao_fila  # Multiplica o tempo de espera pela posição do usuário na fila
        time.sleep(tempo_espera)
        if not is_fila_vazia():
            id_removido = fila.pop(0)
            subprocess.run(['python', 'facecheck.py', '--id', str(id_usuario)])
            bot.send_message(chat_id=id_removido, text="Ainda estamos executando, o processo está em 50%!")
            time.sleep(360)
            bot.send_message(chat_id=message.chat.id, text=f"Seu resultado foi concluído! http://www.facechek.serv00.net/{id_usuario}.html")

    else:
        # Enviar uma resposta ao usuário em caso de falha na detecção de rosto
        bot.reply_to(message, "Não foi possível detectar um rosto na imagem. Por favor, tente novamente com uma imagem diferente.")


@bot.message_handler(commands=['start'])
def start_command(message):
    # Obtém informações do usuário
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_username = message.from_user.username
    user_number = message.from_user.phone_number if hasattr(message.from_user, 'phone_number') else None

    # Insere os dados do usuário no banco de dados SQLite
    insert_query = '''
        INSERT INTO users (telegram_id, name, username, number, email, balance, password)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    user_data = (user_id, user_name, user_username, user_number, None, None, None)
    cursor.execute(insert_query, user_data)
    conn.commit()

    bot.reply_to(message, "Seja bem vindo(a)! Já pensou buscar pessoas pessoas em volta do mundo parecidas com você? Use o comando: /buscar_sosia e tente! Qualquer dúvida, crítica ou sugestão, entre em contato comigo no Instagram: @iamkingheron ou @kingsronr!")


# Iniciar o bot
bot.polling()