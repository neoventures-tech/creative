"""
Tools para o agente RAG.

Define as ferramentas que o agente pode usar durante a conversa.
O contexto é passado via ToolRuntime para ser thread-safe.
"""
import os
from typing import TYPE_CHECKING
from langchain.tools import tool, ToolRuntime
from openai import OpenAI
import google.generativeai as genai

if TYPE_CHECKING:
    from agents.models import Conversation
    from langchain_core.retrievers import BaseRetriever


class AgentContextSchema:
    """Schema do contexto passado para as tools via ToolRuntime."""
    conversation: "Conversation"
    retriever: "BaseRetriever"


@tool
def search_documents(query: str, runtime: ToolRuntime) -> str:
    """
    Busca documentos relevantes na base de conhecimento.

    Use esta ferramenta SEMPRE que precisar buscar informações para responder
    perguntas do usuário. Busque nos documentos disponíveis antes de responder.

    Args:
        query: A consulta/pergunta para buscar nos documentos.

    Returns:
        Conteúdo dos documentos relevantes encontrados.
    """
    retriever = getattr(runtime.context, "retriever", None)

    if not retriever:
        return "Erro: Nenhum retriever configurado para busca de documentos."

    docs = retriever.invoke(query)

    if not docs:
        return "Nenhum documento relevante encontrado para esta consulta."

    return "\n\n---\n\n".join([d.page_content for d in docs])



@tool
def generate_image(
    prompt: str,
    runtime: ToolRuntime,
    size: str = "1536x1024",
) -> str:
    """
      Edita uma imagem usando gpt-image-1 (image-to-image) mantendo o estilo da imagem de referência.

    QUANDO USAR:
    - Quando o usuário pedir para modificar uma imagem mantendo o estilo
    - Quando houver uma imagem de referência e mudanças específicas a fazer
    - Para criar variações de imagens existentes

    REGRAS:
    1. O prompt deve descrever as mudanças desejadas
    2. A imagem de referência serve como base para estilo e layout
    3. Requer organização OpenAI verificada

    Args:
        reference_image_path: Caminho para a imagem de referência
        prompt: Descrição das modificações desejadas
        size: Tamanho da imagem. Opções: "256x256", "512x512", "1024x1024", "1536x1024", "1024x1536"

    Returns:
        str: Caminho da imagem gerada ou mensagem de erro
    """
    try:
        print("\n" + "="*80)
        print("🎨 INICIANDO GERAÇÃO DE IMAGEM")
        print("="*80)

        import base64
        from pathlib import Path
        from agents.models import GeneratedImage

        print("\n[1/6] Extraindo contexto...")
        try:
            conversation = runtime.context.conversation
            reference_image_path = runtime.context.reference_image_path
            print(f"✓ Contexto extraído")
            print(f"   - Conversation ID: {conversation.id if conversation else 'None'}")
            print(f"   - Imagem referência: {reference_image_path}")
        except Exception as e:
            print(f"✗ ERRO ao extrair contexto: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao extrair contexto: {str(e)}"

        if not conversation:
            return "Erro: Conversa não encontrada no contexto."

        print("\n[2/6] Validando parâmetros...")
        try:
            # Validar tamanho
            valid_sizes = ["256x256", "512x512", "1024x1024", "1536x1024", "1024x1536"]
            if size not in valid_sizes:
                size = "1536x1024"
            print(f"✓ Tamanho validado: {size}")

            # Verificar se o arquivo existe
            if not Path(reference_image_path).exists():
                return f"Erro: Imagem de referência não encontrada: {reference_image_path}"
            print(f"✓ Arquivo de referência encontrado")
        except Exception as e:
            print(f"✗ ERRO na validação: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro na validação: {str(e)}"

        print("\n[3/6] Inicializando cliente OpenAI...")
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
            print("✓ Cliente OpenAI inicializado")
        except Exception as e:
            print(f"✗ ERRO ao inicializar cliente: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao inicializar cliente OpenAI: {str(e)}"

        print("\n[4/6] Preparando prompt...")
        try:
            full_prompt = f"""
Mantenha FIELMENTE o layout e estilo da imagem de referência (template).

⚠️ CRÍTICO: Siga EXATAMENTE a estrutura visual do template.

{prompt}

---

ESTRUTURA OBRIGATÓRIA (seguir template EXATAMENTE):
1. **CABEÇALHO SUPERIOR**
   - Faixa horizontal azul escuro no topo.
   - Texto em branco no centro começando com: "COMO PODEMOS..." seguido da pergunta do desafio.

2. **PARTE ESQUERDA / CENTRO – CONTEXTO E PROBLEMA**
   - Ilustrações em estilo cartoon técnico (equipamentos de mineração, operadores, processos, ambiente).
   - Mostrar a situação atual e os problemas visuais (ex.: poeira, fumaça, vibração, sujeira, sucata, risco).
   - Incluir pequenos textos próximos aos elementos, rótulos e explicações.
   - Incluir ícones de alerta (triângulos vermelhos), setas, destaques e observações.
   - Pode ter medições, gráficos simples, balões de fala ou anotações práticas.
   - Mostrar erros, limitações ou dificuldades do processo atual.

3. **BLOCO DIREITO – OBJETIVOS E BENEFÍCIOS**
   - Criar um retângulo vertical em bege/amarelo claro.
   - Dentro dele, incluir uma lista de itens marcados com estrelas (★).
   - Cada item deve representar benefícios, melhorias ou resultados esperados.
   - Acima da caixa, inserir um ícone de alvo, indicando o "objetivo da solução".

4. **ESTILO VISUAL**
   - Estilo cartoon coerente, linhas grossas, contornos marcados, sombras leves.
   - Paleta padrão: azul escuro, amarelo, bege, vermelho para alertas, tons suaves.
   - Pequenas legendas espalhadas explicando elementos.
   - Mistura equilibrada entre imagens e texto.

5. **RODAPÉ**
   - Colocar logos da empresa do desafio à esquerda.
   - Colocar o logo "mininghub." à direita.
   - Fundo cinza muito claro.

6. **NARRATIVA VISUAL**
   - O lado esquerdo sempre representa o PROBLEMA.
   - O lado direito sempre representa a SOLUÇÃO / BENEFÍCIOS.
   - Incluir sempre um contraste claro entre o “antes” e o “depois”.

Mantenha exatamente esse layout em todas as próximas criações.
Inclua apenas os elementos específicos do desafio atual conforme fornecido.

IMPORTANTE: Manter PROPORÇÕES e POSICIONAMENTO do template original.
"""
            print(f"✓ Prompt preparado ({len(full_prompt)} caracteres)")
        except Exception as e:
            print(f"✗ ERRO ao preparar prompt: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao preparar prompt: {str(e)}"

        print("\n[5/6] Chamando API OpenAI para editar imagem...")
        try:
            # Abrir e enviar a imagem de referência
            with open(reference_image_path, "rb") as image_file:
                print(f"   Enviando arquivo: {reference_image_path}")
                response = client.images.edit(
                    # model="gpt-image-1",
                    model="gpt-image-1-mini",
                    image=image_file,
                    prompt=full_prompt,
                    size=size,
                    n=1
                )
            print("✓ API respondeu com sucesso")
        except Exception as e:
            print(f"✗ ERRO na chamada da API OpenAI: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro na API OpenAI: {str(e)}"

        print("\n[6/6] Salvando imagem...")
        try:
            # Obter a imagem resultante (base64)
            output_bytes = base64.b64decode(response.data[0].b64_json)
            print(f"✓ Imagem decodificada ({len(output_bytes)} bytes)")

            # Salvar a imagem localmente
            output_dir = Path("media/generated_images")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_filename = f"edited_{Path(reference_image_path).stem}_{conversation.id}.png"
            output_path = output_dir / output_filename

            with open(output_path, "wb") as f:
                f.write(output_bytes)
            print(f"✓ Arquivo salvo: {output_path}")

            # Salvar no banco (usar caminho relativo começando com /media/)
            # Converter caminho absoluto para URL relativa
            image_url = f"/{output_path}"  # Adiciona / no início para URL absoluta

            generated_image = GeneratedImage.objects.create(
                conversation=conversation,
                prompt=full_prompt,
                image_url=image_url,
                model="gpt-image-1",
                size=size,
                quality="standard",
            )
            print(f"✓ Registro criado no banco (ID: {generated_image.id})")
            print(f"   URL da imagem: {image_url}")

            print("\n" + "="*80)
            print("✅ IMAGEM GERADA COM SUCESSO")
            print("="*80 + "\n")

            return f"✅ Imagem editada com sucesso!\n\nArquivo salvo em: {output_path}\n\nURL: {image_url}"

        except Exception as e:
            print(f"✗ ERRO ao salvar imagem: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao salvar imagem: {str(e)}"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Erro ao editar imagem: {str(e)}"


@tool
def generate_image_gemini(
    prompt: str,
    runtime: ToolRuntime,
    aspect_ratio: str = "16:9",
) -> str:
    """
    Gera uma imagem usando Gemini 3 Pro Image Generation API (image-to-image) mantendo o estilo da imagem de referência.

    QUANDO USAR:
    - Quando o usuário pedir para criar/modificar uma imagem usando Gemini
    - Quando quiser usar o modelo Gemini para geração de imagens de alta qualidade
    - Para criar variações mantendo estilo da imagem de referência

    REGRAS:
    1. O prompt deve descrever as mudanças/conteúdo desejado
    2. A imagem de referência serve como base para estilo e layout
    3. Usa o modelo gemini-3-pro-image-preview para geração de alta qualidade (até 2K)

    Args:
        prompt: Descrição da imagem desejada ou modificações
        aspect_ratio: Proporção da imagem. Opções: "1:1", "16:9", "4:3", "9:16", "3:4"

    Returns:
        str: Caminho da imagem gerada ou mensagem de erro
    """
    try:
        print("\n" + "="*80)
        print("🎨 INICIANDO GERAÇÃO DE IMAGEM COM GEMINI")
        print("="*80)

        import base64
        from pathlib import Path
        from agents.models import GeneratedImage
        from PIL import Image
        import io

        print("\n[1/6] Extraindo contexto...")
        try:
            conversation = runtime.context.conversation
            reference_image_path = runtime.context.reference_image_path
            print(f"✓ Contexto extraído")
            print(f"   - Conversation ID: {conversation.id if conversation else 'None'}")
            print(f"   - Imagem referência: {reference_image_path}")
        except Exception as e:
            print(f"✗ ERRO ao extrair contexto: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao extrair contexto: {str(e)}"

        if not conversation:
            return "Erro: Conversa não encontrada no contexto."

        print("\n[2/6] Validando parâmetros...")
        try:
            # Validar aspect_ratio
            valid_ratios = ["1:1", "16:9", "4:3", "9:16", "3:4"]
            if aspect_ratio not in valid_ratios:
                aspect_ratio = "16:9"
            print(f"✓ Aspect ratio validado: {aspect_ratio}")

            # Verificar se o arquivo existe
            if not Path(reference_image_path).exists():
                return f"Erro: Imagem de referência não encontrada: {reference_image_path}"
            print(f"✓ Arquivo de referência encontrado")
        except Exception as e:
            print(f"✗ ERRO na validação: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro na validação: {str(e)}"

        print("\n[3/6] Inicializando cliente Gemini...")
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return "Erro: GEMINI_API_KEY não configurada no ambiente"

            genai.configure(api_key=api_key)
            print("✓ Cliente Gemini inicializado")
        except Exception as e:
            print(f"✗ ERRO ao inicializar cliente: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao inicializar cliente Gemini: {str(e)}"

        print("\n[4/6] Preparando prompt e imagem...")
        try:
            # Carregar imagem de referência
            reference_image = Image.open(reference_image_path)
            print(f"✓ Imagem carregada: {reference_image.size}")

            full_prompt = f"""
⚠️ CRÍTICO: Siga EXATAMENTE a estrutura visual, cores, proporções e layout da imagem de referência (template).

CONTEÚDO DO DESAFIO:
{prompt}

═══════════════════════════════════════════════════════════════════════════════
INSTRUÇÕES DETALHADAS DE GERAÇÃO - SIGA RIGOROSAMENTE
═══════════════════════════════════════════════════════════════════════════════

🎨 ESTILO VISUAL GERAL:
• Infográfico educativo estilo cartoon técnico profissional
• TODOS os elementos com contornos pretos GROSSOS (3-4px) e bem definidos
• Sombras suaves em elementos para profundidade (offset 2-3px, 20% opacity)
• Cores vibrantes, saturadas mas harmônicas (saturação 70-90%)
• Fundo principal: branco puro (#ffffff) ou cinza muito claro (#f5f5f5)
• Perspectiva frontal ou isométrica leve (10-15° máximo)
• Layout LIMPO, ORGANIZADO, profissional - espaço suficiente entre elementos
• Equilíbrio 60% ilustrações / 40% textos informativos

═══════════════════════════════════════════════════════════════════════════════
🟦 SEÇÃO 1: CABEÇALHO SUPERIOR (15% altura total, 100% largura)
═══════════════════════════════════════════════════════════════════════════════

📐 LAYOUT:
• Posição: topo absoluto, x=0, y=0, largura=100%, altura=15%
• Fundo: azul escuro sólido #1a3a52 ou #2c5f7d (SEM gradiente)
• Borda inferior: linha sutil 1px #ffffff com 20% opacity (opcional)

📝 TEXTO:
• Fonte: Sans-serif bold (Arial Black, Helvetica Bold, Roboto Black)
• Cor: branco puro #ffffff
• Tamanho: 3-4% da altura total da imagem
• Alinhamento: centralizado horizontal e verticalmente
• Formato: CAIXA ALTA (uppercase)
• Estrutura em 2 linhas:
  Linha 1: "COMO PODEMOS [AÇÃO/VERBO PRINCIPAL],"
  Linha 2: "[COMPLEMENTO/OBJETIVO/CONTEXTO]?"
• Kerning: espaçado (letter-spacing: 0.02em)
• Espaçamento entre linhas: 1.2-1.3em

🎯 ELEMENTO SUPERIOR DIREITO (opcional):
• Pequeno ícone branco 2-3% tamanho (⚠️, NR12, norma, etc)
• Posição: canto superior direito, margin 2% das bordas

═══════════════════════════════════════════════════════════════════════════════
🏭 SEÇÃO 2: ÁREA ESQUERDA/CENTRAL - CONTEXTO DO PROBLEMA
(75% largura, 70% altura, entre cabeçalho e rodapé)
═══════════════════════════════════════════════════════════════════════════════

🌍 CONTEXTO AMBIENTAL/LOCAL (fundo da cena):
• Ilustração do ambiente em perspectiva leve ou frontal
• Posição: camada de fundo, cobrindo 75% esquerdo
• Cores suaves para não competir com elementos principais:
  - Céu/fundo: azul claro #87ceeb, #b0d4e3 ou cinza #d3d3d3
  - Estruturas: cinza médio #808080, #999999
  - Elementos naturais: verde #90ee90, marrom #d2b48c
• Elementos específicos por contexto:
  Mineração: porto industrial, correias, silos, guindastes, mina
  Indústria: galpão, telhado metálico, janelas, portas, linha produção
  Escritório: paredes, janelas, estantes, divisórias
  Logística: prateleiras, racks, docas, portões
• Label do local em caixa branca semi-transparente:
  - Fundo: #ffffff 80% opacity
  - Borda: #cccccc 1px
  - Texto: CAIXA ALTA, preto #000000, sans-serif bold
  - Exemplo: "PORTO DE TUBARÃO", "ÁREA DE PRODUÇÃO"
  - Posição: superior esquerdo ou central superior

📦 EQUIPAMENTOS/ELEMENTOS-CHAVE (2-4 itens):
• Posicionar em caixas brancas distribuídas estrategicamente
• NÃO sobrepor - manter espaço 3-5% entre caixas

CAIXA DE EQUIPAMENTO (para cada):
• Dimensões: 15-20% largura x 15-20% altura
• Fundo: branco puro #ffffff
• Borda: cinza #cccccc, 2px, sólida
• Sombra: offset 3px 3px, blur 5px, #000000 15% opacity
• Padding interno: 2% em todos os lados
• Border-radius: 8-10px (cantos levemente arredondados)

ILUSTRAÇÃO DO EQUIPAMENTO (dentro da caixa):
• Estilo: cartoon técnico, contornos pretos grossos 3-4px
• Cores vibrantes e identificáveis:
  - Maquinário pesado: amarelo #ffd700, #ffcc00, laranja #ff9933
  - Estruturas metálicas: cinza #808080, #a0a0a0
  - Detalhes: vermelho #e74c3c, azul #3498db, verde #27ae60
• Proporção: ocupar 70% da caixa, centralizado
• Detalhes técnicos visíveis: rodas, correias, cabines, partes móveis
• Sombra interna sutil para profundidade

LABEL DO EQUIPAMENTO:
• Posição: abaixo da ilustração ou footer da caixa
• Fundo: pode ser colorido (amarelo #fff3cd, azul claro #d1ecf1)
• Texto: CAIXA ALTA, preto #000000, sans-serif bold
• Tamanho fonte: 80% do texto do cabeçalho
• Exemplos: "TRANSPORTADOR TRD13", "EMPILHADEIRA", "SERVIDOR PRINCIPAL"

POSICIONAMENTO SUGERIDO:
• Equipamento 1: superior esquerdo (x=5%, y=20%)
• Equipamento 2: inferior esquerdo (x=5%, y=60%)
• Equipamento 3: centro superior (x=35%, y=18%) - opcional
• Equipamento 4: direita central (x=50%, y=45%) - opcional

👷 PERSONAGENS (2-4 pessoas):
• Estilo: cartoon técnico, proporções humanas realistas
• Altura: 20-25% da altura da seção central
• Contornos: pretos grossos 3-4px
• Sombra no chão: elipse preta #000000 20% opacity

VESTIMENTA POR CONTEXTO:
• Mineração/Porto: capacete amarelo/laranja #ffd700, colete refletivo
  amarelo/laranja com faixas cinza #808080, calça azul/cinza, botas pretas,
  óculos de proteção, máscara se aplicável
• Indústria: capacete branco/amarelo, uniforme azul/cinza #5a7a9e,
  óculos proteção, luvas amarelas
• Saúde: jaleco branco #ffffff, scrubs azul/verde #6fa8dc, touca, máscara,
  luvas látex
• Escritório: camisa social, calça, sem EPI
• Construção: capacete amarelo/laranja, colete laranja #ff6b35,
  botas amarelas, cinto ferramentas

EXPRESSÕES E POSES:
• Rostos visíveis: sobrancelhas franzidas (preocupação), boca aberta (esforço),
  gotas de suor (cansaço)
• Poses dinâmicas: agachado operando, em pé segurando ferramenta,
  apontando para problema, empurrando objeto
• Linhas de movimento: 2-3 linhas curvas próximas ao corpo indicando ação
• Cores de pele: variar entre tons claros #ffd5b4, médios #d19a6b, escuros #8b5a3c

POSICIONAMENTO SUGERIDO:
• Personagem 1: centro-esquerda em ação principal
• Personagem 2: centro-direita interagindo com equipamento
• Personagens 3-4: background em ações secundárias

⚠️ DESTAQUE DO PROBLEMA (elemento central CRÍTICO):
• Posição: centro da composição, elemento focal principal
• Área destacada: 25-30% largura x 25-30% altura

CAIXA DO PROBLEMA:
• Fundo: branco #ffffff ou amarelo muito claro #fffacd
• Borda: vermelha #e74c3c ou amarela #ffd700, 3-4px, sólida ou tracejada
• Pode ser retangular com bordas arredondadas ou circular

ILUSTRAÇÃO DO PROBLEMA:
• Desenhar claramente o problema:
  - Poeira: nuvens cinza #a0a0a0, #808080 com contornos ondulados
  - Vibração: 4-6 linhas onduladas amarelas/vermelhas ao redor do objeto
  - Sujeira: pequenos elementos marrons/pretos espalhados
  - Trabalho manual: pessoa fazendo grande esforço, linhas de tensão
  - Risco: raios vermelhos, símbolos ⚠️, elementos perigosos
• Contornos pretos grossos 3px

TRIÂNGULO DE ALERTA:
• Símbolo: ⚠️ triângulo vermelho #e74c3c ou #ff0000
• Tamanho: 8-10% da altura total
• Posição: adjacente à área do problema (direita ou esquerda)
• Preenchimento: vermelho sólido
• Borda: preta 3px
• Símbolo ! dentro: branco ou amarelo #ffd700

TEXTOS DO PROBLEMA:
• Título principal acima/dentro da caixa:
  - Fundo: vermelho #e74c3c ou amarelo #ffd700
  - Texto: branco ou preto, CAIXA ALTA, sans-serif black
  - Exemplo: "PARADAS PARA LIMPEZA MANUAL", "PROCESSO LENTO"
• Subtextos explicativos (2-4 itens):
  - Fonte menor (70% do título)
  - Pode ter ícones ⚠️ antes
  - Cor: vermelho escuro #c0392b ou preto
  - Exemplos: "⚠️ ESFORÇO FÍSICO INTENSO", "EXPOSIÇÃO A POEIRA E CALOR"
• Setas vermelhas #e74c3c (3px) apontando do texto para elemento visual

📝 TEXTOS E LABELS INFORMATIVOS (3-5 itens):
• Distribuir pela cena, conectados a elementos relevantes

CAIXA DE TEXTO:
• Fundo: branco #ffffff 90% opacity ou amarelo claro #fff9e6
• Borda: cinza #cccccc 1px ou sem borda
• Padding: 1% interno
• Border-radius: 5px
• Sombra sutil: 2px 2px 4px #000000 10% opacity

TEXTO:
• Fonte: sans-serif regular (Arial, Helvetica, Roboto)
• Cor: preto #000000
• Tamanho: 60-70% do texto do cabeçalho
• Conteúdo: informações técnicas factuais
  - Medições: "MÉDIA DE 20 PESSOAS ENVOLVIDAS"
  - Frequências: "LIMPEZAS A CADA SAÍDA DE NAVIO"
  - Condições: "TEMPERATURA MÉDIA 40°C"
  - Limitações: "IMPOSSIBILIDADE DE LIMPEZA COM ÁGUA"

SETAS CONECTORAS:
• Cor: preta #000000, vermelha #e74c3c ou amarela #ffd700
• Largura: 2-3px
• Estilo: sólida com ponta triangular
• Conectar label ao elemento visual correspondente

📊 ÁREA DE MEDIÇÕES/NORMAS (canto inferior):
• Posição: inferior esquerdo ou centro-inferior
• Dimensões: 12-15% largura x 10-12% altura

ELEMENTO 1 - ÍCONE DE NORMA/DOCUMENTO:
• Ilustração: documento/papel estilizado
• Cor: branco #ffffff com borda azul #3498db ou preta
• Tamanho: 5-6% altura
• Label: "NHO 09", "ISO 9001", "NR 12" etc
• Fonte: sans-serif bold, preto

ELEMENTO 2 - DADOS/GRÁFICOS:
• Pequeno gráfico simples: linha ondulada, barra, medidor
• Cores: azul #3498db, vermelho #e74c3c
• Ícone ⚠️ triangular amarelo/vermelho se relevante
• Texto: "MEDIÇÕES PONTUAIS" ou "ANÁLISE TÉCNICA"
• Sub-texto menor: "FEITAS POR CONSULTORIA EXTERNA" ou similar

═══════════════════════════════════════════════════════════════════════════════
🟨 SEÇÃO 3: COLUNA DIREITA - OBJETIVOS (25% largura, 70% altura)
═══════════════════════════════════════════════════════════════════════════════

📐 CONTAINER PRINCIPAL:
• Posição: x=75%, y=15% (após cabeçalho), largura=25%, altura=70%
• Fundo: bege/amarelo claro SÓLIDO #fef9e7, #fff8dc ou #fffacd (SEM gradiente)
• Borda esquerda (opcional): cinza clara #cccccc 1px para separar da área central
• Padding interno: 3% todos os lados

🎯 ÍCONE DE ALVO (topo):
• Símbolo: alvo estilizado 🎯 ou círculos concêntricos
• Cores: vermelho centro #e74c3c, branco #ffffff, vermelho externo
• Tamanho: 6-8% da altura da coluna
• Posição: centralizado horizontal, y=5% do topo da coluna
• Contorno preto 2px

📋 TEXTO DE NORMA (se aplicável):
• Posição: abaixo do ícone de alvo
• Fundo: pode ter caixa branca #ffffff ou transparente
• Texto: "RESPEITAR A NR10 E NR12" ou similar
• Fonte: sans-serif bold, preto #000000
• Tamanho: 70% do tamanho do cabeçalho
• Ícone pequeno de documento ou checkmark antes do texto

⭐ LISTA DE OBJETIVOS (4-6 itens):
• Começar após o ícone/norma (y=15-20% da coluna)
• Espaçamento vertical: 8-10% entre cada item
• Alinhamento: esquerda, com margem esquerda 5%

FORMATO DE CADA ITEM:
• Estrela: ⭐ emoji ou símbolo desenhado
  - Cor: amarela #ffd700 ou dourada #ffcc00
  - Tamanho: 5-6% da altura da coluna
  - Posição: alinhar baseline com primeira linha do texto
  - Contorno preto 2px se desenhada
• Texto do objetivo:
  - Posição: 10% à direita da estrela
  - Largura máxima: 80% da largura da coluna
  - Fonte: sans-serif semi-bold (600-700 weight)
  - Cor: preto puro #000000
  - Tamanho: 65-75% do texto do cabeçalho
  - Line-height: 1.3-1.4 para legibilidade
  - Pode ter 1-2 linhas por objetivo
  - CAIXA ALTA ou Title Case conforme preferência

EXEMPLOS DE CONTEÚDO:
⭐ MELHORIA DAS CONDIÇÕES ERGONÔMICAS E DE SEGURANÇA
⭐ MANUTENÇÃO DA INTEGRIDADE AMBIENTAL
⭐ REDUÇÃO DO TEMPO DE LIMPEZA EM 50%
⭐ AUTOMATIZAÇÃO DO PROCESSO
⭐ DIMINUIÇÃO DE CUSTOS OPERACIONAIS
⭐ AUMENTO DA DISPONIBILIDADE DOS EQUIPAMENTOS

═══════════════════════════════════════════════════════════════════════════════
🏢 SEÇÃO 4: RODAPÉ (100% largura, 10-13% altura, base da imagem)
═══════════════════════════════════════════════════════════════════════════════

📐 LAYOUT:
• Posição: base absoluta, x=0, y=87-90%, largura=100%, altura=10-13%
• Fundo: branco #ffffff ou cinza muito claro #fafafa
• Borda superior (opcional): linha sutil 1px #cccccc

🏭 LOGO ESQUERDO (empresa do desafio):
• Posição: x=5%, centralizado verticalmente
• Altura: 60-70% da altura do rodapé
• Logo vetorial ou alta resolução
• Manter proporções originais
• Cores da marca original
• Exemplos: "VALE", logo da empresa cliente

⚙️ LOGO DIREITO (mininghub):
• Posição: x=85-90%, centralizado verticalmente
• Formato: tipografia moderna, minúscula
• Texto: "mininghub." (COM ponto final)
• Fonte: sans-serif moderna (Montserrat, Roboto, Open Sans)
• Cor: azul escuro #1a3a52 ou preto #000000
• Tamanho: 50-60% da altura do rodapé
• Peso: semi-bold ou bold

═══════════════════════════════════════════════════════════════════════════════
🎨 ESPECIFICAÇÕES TÉCNICAS FINAIS
═══════════════════════════════════════════════════════════════════════════════

PALETA DE CORES COMPLETA (usar EXATAMENTE):
• Azul escuro: #1a3a52, #2c5f7d, #003d5c (cabeçalho, elementos corporativos)
• Azul médio: #3498db, #5a7a9e (detalhes, gráficos)
• Azul claro: #6fa8dc, #87ceeb, #b0d4e3 (céu, fundos)
• Amarelo vibrante: #ffd700, #ffcc00 (equipamentos, destaques)
• Amarelo claro: #fef9e7, #fff8dc, #fffacd (coluna objetivos)
• Laranja: #ff9933, #ff6b35, #f77f00 (equipamentos, detalhes)
• Vermelho: #e74c3c, #ff0000, #d62828, #c0392b (alertas, problemas)
• Verde: #27ae60, #90ee90 (vegetação, elementos positivos)
• Cinza escuro: #4a4a4a, #666666 (estruturas pesadas)
• Cinza médio: #808080, #999999, #a0a0a0 (estruturas, equipamentos)
• Cinza claro: #cccccc, #d3d3d3, #e0e0e0 (bordas, divisores)
• Branco: #ffffff (fundos, textos em azul)
• Preto: #000000 (contornos, textos principais)
• Fundo: #f5f5f5, #fafafa (fundo geral)

TIPOGRAFIA:
• Cabeçalho: Arial Black, Helvetica Bold, Roboto Black, Impact
• Títulos: Arial Bold, Helvetica Bold, Roboto Bold
• Textos: Arial, Helvetica, Roboto, Open Sans
• Labels: Arial, Helvetica, sans-serif

PROPORÇÕES EXATAS:
• Formato: landscape 16:9 (1920x1080, 1600x900, 1280x720 ou similar)
• Cabeçalho: 15% altura (y=0 a y=15%)
• Área central: 70-75% altura (y=15% a y=87%)
• Rodapé: 10-13% altura (y=87% a y=100%)
• Coluna esquerda/central: 75% largura (x=0 a x=75%)
• Coluna direita: 25% largura (x=75% a x=100%)
• Margens: 2-3% em todos os lados internos

HIERARQUIA VISUAL:
1. Maior destaque: Problema central com triângulo ⚠️ vermelho
2. Segundo destaque: Cabeçalho azul com pergunta
3. Terceiro destaque: Coluna de objetivos bege à direita
4. Elementos de suporte: Equipamentos, personagens, contexto
5. Elementos de fundo: Ambiente, textos informativos

CHECKLIST FINAL (TODOS OBRIGATÓRIOS):
✅ Cabeçalho azul escuro (#1a3a52) com pergunta em branco CAIXA ALTA
✅ 2-4 equipamentos em caixas brancas (#ffffff) com bordas cinza (#cccccc)
✅ 2-4 personagens cartoon com EPIs/uniformes do contexto específico
✅ Ambiente/local identificado com label
✅ Problema central destacado com ⚠️ triângulo vermelho grande
✅ 3-5 textos informativos em caixas brancas conectados por setas
✅ Coluna direita bege (#fef9e7) com ícone alvo e 4-6 objetivos com ⭐
✅ Rodapé branco com logo empresa (esquerda) e "mininghub." (direita)
✅ Todos os contornos pretos grossos (3-4px) estilo cartoon
✅ Cores da paleta especificada (nenhuma cor fora da paleta)
✅ Layout limpo, organizado, espaçado, NÃO sobrecarregado
✅ Proporções 15% cabeçalho + 70% área central + 15% rodapé
✅ Formato landscape 16:9

═══════════════════════════════════════════════════════════════════════════════
IMPORTANTE: Gere uma imagem EXTREMAMENTE INFORMATIVA e VISUALMENTE RICA que
permita ao visualizador entender COMPLETAMENTE o problema apenas olhando.
Mantenha FIELMENTE o layout, proporções, cores e estilo do template de referência.
═══════════════════════════════════════════════════════════════════════════════
"""
            print(f"✓ Prompt preparado ({len(full_prompt)} caracteres)")
        except Exception as e:
            print(f"✗ ERRO ao preparar prompt: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao preparar prompt: {str(e)}"

        print("\n[5/6] Chamando API Gemini para gerar imagem...")
        try:
            # Configurar modelo Gemini 3 Pro - mais avançado para geração de imagens
            model = genai.GenerativeModel("gemini-3-pro-image-preview")

            # Gerar imagem
            response = model.generate_content(
                [full_prompt, reference_image],
                generation_config=genai.GenerationConfig(
                    temperature=1.0,
                )
            )

            print("✓ API Gemini respondeu com sucesso")

            # Extrair imagem da resposta
            generated_image = None
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data.mime_type.startswith('image/'):
                    generated_image = part.inline_data.data
                    break

            if not generated_image:
                return "Erro: API Gemini não retornou uma imagem"

        except Exception as e:
            print(f"✗ ERRO na chamada da API Gemini: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro na API Gemini: {str(e)}"

        print("\n[6/6] Salvando imagem...")
        try:
            # Salvar a imagem localmente
            output_dir = Path("media/generated_images")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_filename = f"gemini_{Path(reference_image_path).stem}_{conversation.id}.png"
            output_path = output_dir / output_filename

            with open(output_path, "wb") as f:
                f.write(generated_image)
            print(f"✓ Arquivo salvo: {output_path} ({len(generated_image)} bytes)")

            # Salvar no banco
            image_url = f"/{output_path}"

            generated_image_record = GeneratedImage.objects.create(
                conversation=conversation,
                prompt=full_prompt,
                image_url=image_url,
                model="gemini-3-pro-image-preview",
                size=aspect_ratio,
                quality="high",  # Gemini 3 Pro oferece alta qualidade
            )
            print(f"✓ Registro criado no banco (ID: {generated_image_record.id})")
            print(f"   URL da imagem: {image_url}")

            print("\n" + "="*80)
            print("✅ IMAGEM GERADA COM SUCESSO VIA GEMINI")
            print("="*80 + "\n")

            return f"✅ Imagem gerada com sucesso usando Gemini!\n\nArquivo salvo em: {output_path}\n\nURL: {image_url}"

        except Exception as e:
            print(f"✗ ERRO ao salvar imagem: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao salvar imagem: {str(e)}"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Erro ao gerar imagem com Gemini: {str(e)}"


def get_agent_tools():
    """
    Retorna a lista de tools disponíveis para o agente.

    Returns:
        Lista de tools LangChain.
    """
    return [
        # search_documents,
        # generate_image,
        generate_image_gemini,
    ]