
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Treina uma LoRA para geração de imagens'

    def handle(self, *args, **options):
        from openai import OpenAI
        import os
        import pathlib

        # Inicializa o cliente
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        # Caminho da imagem de referência
        img_path = str(pathlib.Path(__file__).parent.parent.parent / "langchain" / "data" / "template.jpeg")

        # Prompt com as instruções de alteração
        prompt = """
        Gere uma nova imagem mantendo o layout, estilo e paleta da imagem enviada.
        Modifique os textos para abordar o desafio:

        "Como identificar sucata não metálica antes dos britadores da planta de Cuiabá"

📘 Descrição completa da imagem para recriação

A imagem é um infográfico ilustrado com estilo de desenho/cartoon, cores suaves e elementos relacionados à mineração. O tema principal é:

"Como podemos realizar a caracterização de rochas subterrâneas através de fotos de testemunhas de sondagem?"

🎨 Estilo visual

Desenho em estilo ilustrado, com traços grossos e colorização suave.

Personagens e equipamentos têm aparência de cartoon.

Há ícones pequenos (ampulheta, dinheiro, estrela, alvo etc.) para reforçar ideias.

🖼️ Composição geral

A imagem é dividida em dois grandes lados:

⭐ Lado esquerdo – Ilustração da sondagem e explicações técnicas
Topo

Um título grande, em fundo azul:

COMO PODEMOS REALIZAR A CARACTERIZAÇÃO DE ROCHAS SUBTERRÂNEAS ATRAVÉS DE FOTOS DE TESTEMUNHAS DE SONDAGEM?

Ilustração principal

Um cenário de mineração ao ar livre com:

Uma sonda de perfuração inclinada, apoiada sobre o terreno.

A sonda está desenhada com um painel de controle e haste entrando no solo.

No chão há uma linha preta representando o furo de sondagem, com um cilindro indicando o testemunho de sondagem.

Próximo à sonda, há:

Um trabalhador usando capacete e máscara, operando um equipamento sobre um tripé.

Textos explicativos espalhados pela ilustração

Ao lado do trabalhador:

“TESTEMUNHO: avaliar condições estruturais antes da abertura da mina”

“Saber se existe o minério”

“Saber se existem falhas nas rochas”

Em vermelho, no centro:

“Não identifica a posição de descontinuidades maiores”

Ícone triangular de alerta.

Setas indicando consequências:

“Estabilidade de galeria – Segurança”

“Estabilidade da escavação”

“Aumento do custo e perda de tempo”

Ícones de dinheiro voando e ampulheta.

No solo, com setas:

“Perfurações”

“Direção do furo”

“Direção da descontinuidade”

“Testemunho de sondagem”

⭐ Lado direito – Benefícios listados em forma de bullet points

Um quadro de fundo bege claro com uma lista marcada por estrelas. No topo, um ícone de alvo com flecha.

Título do bloco:

● Ganho de eficiência na interpretação de testemunhos

Lista com estrelas:

Padronização e rastreabilidade das informações

Geração de modelos tridimensionais

Redução de risco de instabilidade do maciço

Aumento da taxa de desenvolvimento e redução de custo

Na base, logos:
AngloGold Ashanti e mininghub.

        Não altere a estética geral.
        """

        with open(img_path, "rb") as image_file:
            response = client.images.edit(
                model="gpt-image-1",
                image=image_file,
                prompt=prompt,
                size="1536x1024",
                n=1
            )

        # Obtém a imagem resultante (pode ser URL ou base64)
        import base64

        # Resposta em base64
        output_bytes = base64.b64decode(response.data[0].b64_json)
        print("Imagem recebida em formato base64")

        output_file = "resultado.png"
        with open(output_file, "wb") as f:
            f.write(output_bytes)

        print("Imagem gerada e salva como:", output_file)

