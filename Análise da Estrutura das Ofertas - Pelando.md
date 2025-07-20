# Análise da Estrutura das Ofertas - Pelando

## Estrutura HTML Identificada

O código fornecido mostra uma oferta do site Pelando com a seguinte estrutura:

### Container Principal
- `<li>` com `<div class="_container_hphkd_1">`

### Informações do Usuário
- Avatar: `<img>` com classe `_avatar-image_ih8tl_10`
- Nome: `<span>` dentro de `_nickname-container_1yc4q_1`

### Card da Oferta
- Container: `<div class="_deal-card_1jdb6_25 _default-deal-card_1mw5o_31">`
- Imagem: `<img class="_deal-card-image_1glvo_31">`
- Link: `<a href="https://www.pelando.com.br/d/..."`

### Dados Importantes para Extração

1. **Título da Oferta**: 
   - Seletor: `._title_mszsg_31._default-deal-card-title_1mw5o_71`
   - Exemplo: "(STEAM / Pré-venda) Jogo WUCHANG: Fallen Feathers - PC"

2. **Preço**:
   - Seletor: `._deal-card-stamp_15l5n_25`
   - Exemplo: "R$ 159"

3. **Loja**:
   - Seletor: `._container_13qz9_31._default-deal-card-store_1mw5o_66 a`
   - Exemplo: "Nuuvem"

4. **Link da Oferta**:
   - Seletor: `._title_mszsg_31._default-deal-card-title_1mw5o_71` (atributo href)
   - Exemplo: "https://www.pelando.com.br/d/steam-pre-venda-jogo-wuchang-fallen-feathers-pc-4d49"

5. **Imagem**:
   - Seletor: `._deal-card-image_1glvo_31`
   - Atributo: src

6. **Temperatura (Popularidade)**:
   - Seletor: `._deal-card-temperature_1o9of_29 span`
   - Exemplo: "16°"

7. **Timestamp**:
   - Seletor: `._timestamp_1s0as_25._default-deal-card-timestamp_1mw5o_75`
   - Exemplo: "5 min"

## URL Base
- Site: https://www.pelando.com.br/
- Provavelmente precisaremos acessar a página principal ou uma seção específica de ofertas

## Estratégia de Scraping
1. Acessar a página principal do Pelando
2. Localizar os containers de ofertas
3. Extrair as informações usando os seletores identificados
4. Formatar mensagem para Telegram
5. Enviar via Bot API

