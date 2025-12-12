from django.conf import settings


def load_image_as_input(image_url: str) -> dict:
    """
    Carrega a imagem do disco e retorna um dict aceito pela API do Gemini.
    """
    from urllib.parse import urlparse
    import os

    parsed = urlparse(image_url)
    relative_path = parsed.path.lstrip("/")  # remove leading slash
    abs_path = os.path.join(settings.BASE_DIR, relative_path)

    # Detecta MIME pelo final do nome
    mime = "image/jpeg" if abs_path.lower().endswith(".jpg") or abs_path.lower().endswith(".jpeg") else "image/png"

    with open(abs_path, "rb") as f:
        data = f.read()

    return {
        "mime_type": mime,
        "data": data
    }
