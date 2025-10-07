# Guia para Desenvolvimento da Documentação com MkDocs

Este guia irá ajudá-lo a continuar a desenvolver o seu site de documentação estática gerado com o MkDocs.

## Estrutura de Navegação

O menu de navegação lateral que vê no site é controlado pela secção `nav` no ficheiro `mkdocs.yml`. A estrutura é hierárquica, o que significa que pode aninhar páginas dentro de secções para uma melhor organização.

**Exemplo de estrutura no `mkdocs.yml`:**

```yaml
nav:
  - Home: index.md
  - 'Guia do Utilizador':
    - 'Instalação': 'guia/instalacao.md'
    - 'Configuração': 'guia/configuracao.md'
  - 'Sobre': 'sobre.md'
```

Neste exemplo, 'Guia do Utilizador' seria uma secção no menu que, ao ser clicada, revelaria as páginas 'Instalação' e 'Configuração'.

## Como Adicionar ou Editar Páginas

1.  **Crie ou edite um ficheiro Markdown:** Todos os conteúdos das páginas são escritos em ficheiros Markdown (com a extensão `.md`). Pode criar um novo ficheiro `.md` dentro da pasta `docs/` ou editar um existente.

2.  **Adicione o ficheiro à navegação:** Após criar ou renomear um ficheiro, precisa de o adicionar à secção `nav` no `mkdocs.yml` para que ele apareça no menu. Pode escolher o título que aparecerá no menu e o caminho para o ficheiro.

    ```yaml
    nav:
      - 'Minha Nova Página': 'caminho/para/o/meu/novo_ficheiro.md'
    ```

## Visualizar as Alterações Localmente

Para ver as suas alterações em tempo real antes de as publicar, pode usar o servidor de desenvolvimento do MkDocs.

1.  **Abra o seu terminal** na raiz do projeto.

2.  **Execute o comando:**

    ```bash
    mkdocs serve
    ```

3.  **Abra o seu navegador:** O MkDocs irá mostrar-lhe um endereço local (normalmente `http://127.0.0.1:8000`). Visite este endereço para ver o seu site.

O servidor atualiza automaticamente o site sempre que guardar uma alteração num dos seus ficheiros `.md` ou no `mkdocs.yml`.

## Publicar o seu Site

Quando estiver satisfeito com as suas alterações, pode gerar os ficheiros HTML estáticos para o seu site.

1.  **Execute o comando de construção:**

    ```bash
    mkdocs build
    ```

2.  **Ficheiros gerados:** O MkDocs irá criar uma nova pasta chamada `site/` na raiz do seu projeto. Esta pasta contém todos os ficheiros HTML, CSS e JavaScript do seu site.

3.  **Publicação:** Pode publicar o conteúdo da pasta `site/` em qualquer serviço de alojamento de sites estáticos, como o GitHub Pages, Netlify, Vercel, etc.

## Dicas Adicionais

*   **Limpeza de Ficheiros:** Como mencionou, tem muitos ficheiros. Pode apagar os ficheiros `.md` que não quer na sua documentação final. Lembre-se de os remover também da secção `nav` no `mkdocs.yml`.
*   **Títulos:** Pode melhorar os títulos no `mkdocs.yml` para serem mais descritivos e fáceis de ler. O que aparece no menu é o texto que define antes do nome do ficheiro.

Espero que este guia o ajude a continuar a desenvolver a sua documentação!