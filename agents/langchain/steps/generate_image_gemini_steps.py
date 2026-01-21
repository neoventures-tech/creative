from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig


def step_extract_context(
        runtime: ToolRuntime,
        config: RunnableConfig,
):
    print("\n[1/6] Extraindo contexto...")

    # 1️⃣ Tentativa primária (quando LangChain propaga)
    context = getattr(runtime, "context", None)

    # 2️⃣ Fallback ABSOLUTO (sempre confiável)
    if context is None and config:
        context = config.get("context")

    if context is None:
        raise RuntimeError(
            "Contexto não encontrado nem no ToolRuntime nem no RunnableConfig."
        )

    conversation = getattr(context, "conversation", None)
    ref_img = getattr(context, "reference_image_path", None)
    layout_img = getattr(context, "reference_layout_image_path", None)

    if not conversation:
        raise RuntimeError("Conversation ausente no contexto.")

    if not ref_img or not layout_img:
        raise RuntimeError("Imagens de referência ausentes no contexto.")

    print("✓ Contexto resolvido com sucesso")
    return conversation, ref_img, layout_img


def step_validate_params(aspect_ratio: str, reference_image_path: str) -> str:
    valid_ratios = ["1:1", "16:9", "4:3", "9:16", "3:4"]
    if aspect_ratio not in valid_ratios:
        aspect_ratio = "16:9"

    from pathlib import Path
    if not Path(reference_image_path).exists():
        raise FileNotFoundError(
            f"Imagem de referência não encontrada: {reference_image_path}"
        )

    return aspect_ratio


def step_init_gemini_client():
    import os
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY não configurada")

    genai.configure(api_key=api_key)


def step_prepare_reference_images_from_state(
        conversation,
        reference_image_path: str,
        reference_layout_image_path: str,
        state: dict,
):
    from PIL import Image
    from pathlib import Path
    from django.conf import settings

    layout_reference = Image.open(reference_layout_image_path)

    reference_image = None
    image_attachments = []

    # --------------------------------------------------
    # 1️⃣ Edit mode (reply image)
    # --------------------------------------------------
    reply_image_message = state.get("reply_image_message")
    if reply_image_message:
        relative_path = reply_image_message.replace(settings.MEDIA_URL, "")
        full_path = Path(settings.MEDIA_ROOT) / relative_path
        if full_path.exists():
            reference_image = Image.open(full_path)

    # --------------------------------------------------
    # 2️⃣ Attachments (Django InMemoryUploadedFile OR dict)
    # --------------------------------------------------
    attachments = state.get("attachments", [])

    for a in attachments:
        # Case A: Django UploadedFile
        if hasattr(a, "content_type") and a.content_type.startswith("image/"):
            image_attachments.append(Image.open(a))

        # Case B: normalized dict (future-proof)
        elif isinstance(a, dict):
            mime = a.get("mime_type", "")
            path = a.get("path")
            if mime.startswith("image/") and path:
                image_attachments.append(Image.open(path))

    # Promote first attachment to reference if needed
    if reference_image is None and image_attachments:
        reference_image = image_attachments[0]

    # --------------------------------------------------
    # 3️⃣ Fallback template
    # --------------------------------------------------
    if reference_image is None:
        reference_image = Image.open(reference_image_path)

    return reference_image, layout_reference, image_attachments


def step_call_gemini_api(
        prompt: str,
        reference_image,
        layout_reference=None,
        image_attachments=None,
):
    """
    Calls Gemini Image API with:
    - prompt (text)
    - reference image (canvas)
    - optional layout reference
    - optional attachment images (assets like logos)
    """

    import google.generativeai as genai

    model = genai.GenerativeModel("gemini-3-pro-image-preview")

    # --------------------------------------------------
    # Build multimodal input payload
    # --------------------------------------------------
    inputs = [prompt]

    if reference_image is not None:
        inputs.append(reference_image)

    if layout_reference is not None:
        inputs.append(layout_reference)

    if image_attachments:
        for img in image_attachments:
            inputs.append(img)

    # --------------------------------------------------
    # Call Gemini
    # --------------------------------------------------
    response = model.generate_content(
        inputs,
        generation_config=genai.GenerationConfig(
            temperature=1.0
        ),
    )

    # --------------------------------------------------
    # Extract generated image
    # --------------------------------------------------
    for part in response.parts:
        if (
                hasattr(part, "inline_data")
                and part.inline_data.mime_type.startswith("image/")
        ):
            print("✓ Imagem recebida da API Gemini")
            return part.inline_data.data

    raise RuntimeError("API Gemini não retornou imagem")


def step_save_image(
        conversation,
        prompt: str,
        image_bytes: bytes,
        aspect_ratio: str,
) -> str:
    from pathlib import Path
    from datetime import datetime
    from django.conf import settings
    from agents.models import GeneratedImage

    output_dir = Path(settings.MEDIA_ROOT) / "generated_images"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gemini_{timestamp}_{conversation.id}.png"
    output_path = output_dir / filename

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    image_url = f"{settings.MEDIA_URL}generated_images/{filename}"

    record = GeneratedImage.objects.create(
        conversation=conversation,
        prompt=prompt,
        image_url=image_url,
        model="gemini-3-pro-image-preview",
        size=aspect_ratio,
        quality="high",
    )

    print("✓ Imagem salva com sucesso")
    print(f"   - Arquivo: {output_path}")
    print(f"   - URL: {image_url}")

    return f"✅ Imagem gerada com sucesso!\nURL: {image_url}"