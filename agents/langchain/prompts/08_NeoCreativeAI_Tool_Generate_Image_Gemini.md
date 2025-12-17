# Explicação da Tool generate_image_gemini

Este arquivo explica de forma objetiva e sem redundância a tool `generate_image_gemini`, disponível para uso pelo agente.

---

## O que a Tool Faz

A tool `generate_image_gemini` executa a **geração ou edição de imagens** utilizando o modelo **Gemini 3 Pro**, seguindo um pipeline técnico fixo.

Ela recebe um prompt já finalizado pelo agente e transforma esse prompt em uma imagem, respeitando:

* contexto da conversa
* estado de execução
* imagens de referência
* imagem de layout estrutural

A tool **não decide conteúdo**, apenas executa.

---

## Quando Usar

Use esta tool sempre que o agente precisar:

* gerar uma nova imagem
* editar uma imagem existente
* aplicar um layout visual obrigatório
* utilizar imagens de referência fornecidas pelo sistema

---

## Parâmetros Recebidos

A tool recebe três parâmetros:

* prompt: texto final que descreve exatamente a imagem a ser gerada ou editada
* runtime: mantido apenas por compatibilidade (não é fonte de dados)
* config: RunnableConfig, que contém todo o contexto real de execução

---

## Fonte de Verdade

Toda a informação necessária para execução vem de:

config.configurable

Dentro desse objeto, a tool espera encontrar um **AgentContext** válido.

---

## AgentContext Necessário

O AgentContext deve conter:

* conversation: referência da conversa ativa
* reference_image_path: caminho opcional para imagem base
* reference_layout_image_path: caminho opcional para imagem de layout

Sem esse contexto, a tool falha.

---

## Uso do State

O state é opcional e ajusta o comportamento da geração.

Campos utilizados:

* reply_image_message: define modo edição quando presente
* attachments: imagens anexadas à conversa
* aspect_ratio: proporção da imagem (padrão 16:9)

---

## Modos de Operação

Modo Geração

* Ativado quando não há reply_image_message
* Cria uma nova imagem a partir do prompt

Modo Edição

* Ativado quando reply_image_message está presente
* Modifica uma imagem existente

---

## Pipeline Interno

A execução sempre segue estas etapas, nesta ordem:

1. Validação de contexto e parâmetros
2. Inicialização do cliente Gemini
3. Preparação das imagens de referência
4. Chamada da API Gemini
5. Salvamento da imagem gerada

O pipeline é determinístico e não adaptativo.

---

## Logging e Erros

A tool registra cada etapa do pipeline.

Se ocorrer qualquer erro:

* a execução é interrompida
* o erro é registrado
* a exceção é propagada para o agente

Não existe fallback silencioso.

---

## Limites da Tool

A tool:

* não interpreta intenção do usuário
* não cria regras visuais
* não altera o prompt
* não decide layout ou estilo

Essas decisões são responsabilidade exclusiva do agente.

---

## Resumo Operacional

A tool `generate_image_gemini` deve ser tratada como um **executor técnico confiável**.

O agente:

* pensa
* decide
* constrói o prompt

A tool:

* executa
* gera ou edita a imagem
* retorna o resultado
