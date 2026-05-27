# 📐 Guia de Ajustes do Layout - Template ONS 2026

## Status Atual do PDF Gerado

✅ **Diagnóstico do Template**

- Tamanho: 960pt × 540pt (13.3" × 7.5") - Paisagem A4
- Total de páginas: 9
- Configuração de margens via LAYOUT_CONFIG em `palkia_pdf_componentes.py`

## Estrutura de Distribuição de Slides

```
CAPA (página 0)
├─ Margem top: 250px (3.47")
├─ Usa template_page: 0 (primeira página do template)
└─ Título centralizado com fontSize=42

CONTEÚDO (páginas 1-5)
├─ Margem top: 140px (1.94")
├─ Usa template_page: 2 (página padrão de conteúdo)
├─ Título com fontSize=34
└─ Corpo com fontsize=16 + bullets

ENCERRAMENTO (página 6)
├─ Margem top: 280px (3.89")
├─ Usa template_page: 8 (última página do template)
└─ Título centralizado
```

## Conversão de Unidades

```
1 polegada (inch) = 72 pontos = 2.54 cm

Pixels para Pontos (aproximado):
- 72 pt = 1 inch = ~96 px
- 1 px ≈ 0.75 pt
- 1 pt ≈ 1.33 px (ou 1/72 inch)

Conversão rápida:
- 250 px = 3.47 inch = 8.81 cm
- 140 px = 1.94 inch = 4.93 cm  
- 280 px = 3.89 inch = 9.88 cm
- 100 px = 1.39 inch = 3.53 cm (margens laterais)
```

## Como Fazer Ajustes Finos

### 1️⃣ Ajustar Margem Superior (TOP)

**Problema**: Texto saindo do topo ou muito longe
**Solução**: Modificar em `palkia_pdf_componentes.py`

```python
LAYOUT_CONFIG = {
    "CAPA": {
        "top": 250,      # ← AJUSTE AQUI (aumentar = desce mais)
        "bottom": 200,
        "left": 100,
        "right": 100,
        "template_page": 0,
    },
    ...
}
```

**Referência Visual**:

- **top=200**: Mais próximo do topo (sobe ~50px)
- **top=250**: Padrão atual (centro-ish)
- **top=300**: Mais para baixo (desce ~50px)

### 2️⃣ Ajustar Margens Laterais (LEFT/RIGHT)

**Problema**: Texto tocando bordas ou muito espaço livre
**Solução**: Modificar LEFT/RIGHT em LAYOUT_CONFIG

```python
"CONTEUDO": {
    "top": 140,
    "bottom": 110,
    "left": 100,      # ← ESPAÇO DA ESQUERDA
    "right": 100,     # ← ESPAÇO DA DIREITA
    "template_page": 2,
},
```

**Como interpretar**:

- `left=100` + `right=100` com página 960pt → conteúdo usa ~760pt
- Aumentar para `left=120` → conteúdo fica mais centralizado

### 3️⃣ Ajustar Margens Inferiores (BOTTOM)

**Problema**: Espaço inadequado antes da próxima página
**Solução**: Modificar BOTTOM

```python
"ENCERRAMENTO": {
    "top": 280,
    "bottom": 200,    # ← ESPAÇO DO RODAPÉ
    ...
}
```

## Workflow de Ajuste Recomendado

### Passo 1: Fazer um Ajuste Pequeno

```python
# Em palkia_pdf_componentes.py
"CONTEUDO": {
    "top": 140,        # Original
    # ... tente: 130, 150, 160
}
```

### Passo 2: Executar Script

```bash
python script_ons_template.py
```

Você verá algo como:

```
Slide  1: [CONTEUDO    ] → top=140px, bottom=110px, left=100px, right=100px
```

### Passo 3: Verificar PDF Gerado

Abra: `assets/apresentacao_ONS_PLC_TEMPLATE.pdf`

### Passo 4: Registrar Valores Ideais

Quando encontrar valores que funcionem bem, documente aqui:

**✅ AJUSTES IDEAIS ENCONTRADOS**

```
CAPA:
- top: 250px ✓
- bottom: 200px ✓
- left: 100px ✓
- right: 100px ✓

CONTEUDO:
- top: 140px → AJUSTAR PARA: ___px
- bottom: 110px → AJUSTAR PARA: ___px
- left: 100px → AJUSTAR PARA: ___px
- right: 100px → AJUSTAR PARA: ___px

ENCERRAMENTO:
- top: 280px → AJUSTAR PARA: ___px
- bottom: 200px → AJUSTAR PARA: ___px
- left: 100px → AJUSTAR PARA: ___px
- right: 100px → AJUSTAR PARA: ___px
```

## Debug Avançado

### Ver Dimensões do Conteúdo Real

Adicione esta função em `script_ons_template.py`:

```python
def analyze_content_pdf(pdf_path):
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    for i, page in enumerate(reader.pages):
        print(f"Página {i}: {page.mediabox.width:.0f}pt × {page.mediabox.height:.0f}pt")
        print(f"  Cropbox: {page.cropbox}")
```

### Validar Merge Correto

Verifique se os PDFs estão sendo mesclados corretamente:

- Conteúdo gerado em `temp_content.pdf`
- Template em `assets/Template PPT ONS 2026 (2).pdf`
- Resultado final em `assets/apresentacao_ONS_PLC_TEMPLATE.pdf`

## Próximos Passos

1. ✅ Script básico funcionando
2. ⏳ **Ajustar margens via LAYOUT_CONFIG**
3. ⏳ Validar visualmente no PDF
4. ⏳ Otimizar tamanho de fontes se necessário
5. ⏳ Adicionar numeração de páginas (opcional)

---

**Data de atualização**: 13 de maio de 2026
**Versão do script**: v3 com diagnóstico
