import re


class PipelineLogger:
    def __init__(self, total_steps):
        self.total_steps = total_steps

    def start(self, title="PROCESS STARTED"):
        print("\n" + "=" * 80)
        print(f"🔍 {title}")
        print("=" * 80)

    def step(self, step=None, message=None, icon=""):
        if self.total_steps:
            print(f"\n{icon} [{step}/{self.total_steps}] {message}")
            return
        print(f"\n{icon} {message}")

    def step_success(self, message="Concluído com sucesso"):
        print(f"   ✓ {message}")

    def step_error(self, message="Erro ao executar a etapa", details=None):
        print(f"   ✗ {message}")
        if details:
            print(f"     ↳ {details}")

    def error(self, message="PROCESS FAILED", exception=None):
        print("\n" + "=" * 80)
        print(f"❌ {message}")
        if exception:
            print(f"💥 {exception}")
        print("=" * 80 + "\n")

    def success(self, message="PROCESS FINISHED SUCCESSFULLY"):
        print("\n" + "=" * 80)
        print(f"✅ {message}")
        print("=" * 80 + "\n")


def md_to_token_friendly(md_text: str) -> str:
    """
    Converte um Markdown rico em um texto token-friendly para LLM.
    Preserva significado, remove formatação e redundância.
    """

    text = md_text

    # Remove blocos de código
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove cabeçalhos markdown (#, ##, ###)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Remove listas markdown (-, *, •)
    text = re.sub(r"^[\-\*\•]\s*", "- ", text, flags=re.MULTILINE)

    # Remove negrito, itálico
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)

    # Remove separadores
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)

    # Remove emojis (opcional, mas reduz tokens)
    text = re.sub(r"[^\w\s.,:;!?()/#%-]", "", text)

    # Colapsa múltiplas linhas
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove espaços extras
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def _get_attachment_type(file):
    content_type = getattr(file, "content_type", "")

    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("audio/"):
        return "audio"
    if content_type.startswith("video/"):
        return "video"
    return "file"
