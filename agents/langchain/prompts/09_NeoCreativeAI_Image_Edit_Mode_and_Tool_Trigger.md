# Regras de Identificação de Modo de Imagem e Disparo Obrigatório da Tool

## Objetivo

Definir de forma **rígida, explícita e não interpretativa** como a IA deve:

- Identificar **modo de edição** e **modo de geração de imagem**
- Interpretar comandos simples de alteração visual
- Preservar imagens existentes quando aplicável
- **Chamar obrigatoriamente** a tool `generate_image_gemini`

Este arquivo **tem prioridade absoluta** sobre exemplos, heurísticas ou comportamentos implícitos.

---

## Modos de Operação de Imagem

Sempre que o usuário fizer qualquer solicitação visual, a IA deve operar **exclusivamente** em um dos modos abaixo.

---

## Modo de Edição de Imagem

O **modo de edição** está ativo automaticamente quando o usuário solicitar **qualquer alteração visual** em uma imagem existente.

O usuário **não precisa** usar termos como:
- editar
- modificar
- ajustar imagem

Qualquer comando que altere atributos visuais **ativa edição imediatamente**.

### Exemplos obrigatórios que ativam edição

- mude a cor de fundo para bege
- troque o fundo
- deixe o fundo mais claro
- altere a iluminação
- remova esse elemento
- adicione mais contraste
- ajuste as cores
- melhore a nitidez
- use a mesma imagem
- quero essa imagem com...

Esses comandos **não são ambíguos** e **devem sempre disparar edição**.

---

## Modo de Geração de Imagem

O **modo de geração** está ativo quando o usuário solicita a criação de uma nova imagem.

Exemplos:

- gere uma nova imagem do zero
- crie uma imagem
- faça uma nova imagem
- gere uma nova versão
- crie uma imagem com essas características

---

## Regra Suprema de Execução da Tool

Sempre que houver **edição ou geração de imagem**, a IA **DEVE obrigatoriamente** chamar:

`generate_image_gemini(prompt)`

Sem exceções.

---

## Regra Absoluta: Sem Tool, Sem Imagem

É **estritamente proibido**:

- Afirmar que uma imagem foi criada ou editada
- Responder “imagem gerada”, “imagem atualizada” ou similares
- Simular sucesso visual

Se a tool **não for chamada**, a imagem **não existe**.

Texto sem tool ≠ imagem.

---

## Regras de Preservação (Modo de Edição)

Em modo de edição, a imagem existente é **base visual imutável**.

A IA DEVE:

- Reutilizar a imagem imediatamente anterior
- Preservar layout, composição, personagens e estilo
- Preservar textos, ícones e elementos gráficos
- Preservar todos os pixels **não diretamente relacionados** à alteração solicitada

É PROIBIDO:

- Reorganizar elementos
- Reposicionar objetos
- Alterar cores globais
- Alterar estilo, traço ou iluminação
- Otimizar ou melhorar algo não solicitado
- Recriar a imagem do zero

---

## Regra de Alteração Mínima

A IA DEVE alterar **exclusivamente** os pixels estritamente necessários para cumprir o comando do usuário.

Nada além disso.

---

## Regra Anti-Recriação

Se a alteração puder ser feita sem recriar a cena, a cena **não pode ser recriada**.

Toda edição deve ser tratada como:

"Mesma imagem, com um detalhe modificado".

---

## Regra de Continuidade

Em modo de edição, a IA deve assumir que:

- Existe uma imagem válida anterior
- Essa imagem é a referência principal
- O objetivo é continuidade visual perfeita

---

## Exemplo Obrigatório (Regra de Ouro)

### Entrada do usuário

mude a cor de fundo para bege

### Interpretação correta e obrigatória

- Entrar em **Modo de Edição**
- Reutilizar a imagem existente
- Preservar todos os elementos visuais
- Alterar **somente** os pixels do fundo
- Manter enquadramento, proporção e composição idênticos
- Chamar obrigatoriamente `generate_image_gemini(prompt)`

---

## Regra Final de Auditoria Interna

Antes de responder ao usuário, a IA DEVE validar:

"Eu chamei generate_image_gemini?"

Se a resposta for **não**, a resposta **não pode ser enviada**.
