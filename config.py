import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Usada pelo Flask para assinar a sessão e as mensagens (flash)
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-de-desenvolvimento")

    # Tamanho máximo do arquivo enviado: 16 MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
