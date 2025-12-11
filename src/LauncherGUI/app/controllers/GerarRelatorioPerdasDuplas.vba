'============================================
' GERADOR DE RELATÓRIOS PERDAS DUPLAS - VERSÃO FINAL
'============================================
Option Explicit

' ======================
' SUB PRINCIPAL - BOTÃO
' ======================
Sub GerarRelatorioPerdasDuplasETL()
    On Error GoTo ErroHandler
    
    Dim templateWord As String
    Dim pagina As Long
    Dim incluirTeste As Boolean
    Dim converterPDF As Boolean
    
    ' 1. ESCOLHER ARQUIVO WORD
    Debug.Print "1. Escolhendo arquivo Word..."
    templateWord = Application.GetOpenFilename( _
        FileFilter:="Arquivos Word (*.docx; *.doc), *.docx; *.doc", _
        Title:="Selecione o Template Word")
    
    If templateWord = "False" Then
        Debug.Print "Usuário cancelou escolha do Word"
        Exit Sub
    End If
    
    ' 2. PERGUNTAR NÚMERO DA PÁGINA
    Debug.Print "2. Perguntando número da página..."
    Dim respostaPagina As String
    respostaPagina = InputBox("Em qual página deseja inserir a tabela?" & vbCrLf & _
                            "Digite um número (ex: 1, 2, 3...):", _
                            "Número da Página", "1")
    
    If respostaPagina = "" Then
        Debug.Print "Usuário cancelou input da página"
        Exit Sub
    End If
    
    If Not IsNumeric(respostaPagina) Then
        MsgBox "Por favor, digite um número válido!", vbExclamation
        Exit Sub
    End If
    
    pagina = CLng(respostaPagina)
    
    ' 3. PERGUNTAR SE INCLUI TABELA DE TESTE
    Debug.Print "3. Perguntando sobre tabela de teste..."
    If MsgBox("Deseja incluir tabela de teste de formatação?", _
              vbYesNo + vbQuestion, "Tabela de Teste") = vbYes Then
        incluirTeste = True
    Else
        incluirTeste = False
    End If
    
    ' 4. PERGUNTAR SE CONVERTE PARA PDF
    Debug.Print "4. Perguntando sobre PDF..."
    If MsgBox("Deseja converter para PDF após gerar?", _
              vbYesNo + vbQuestion, "Converter para PDF") = vbYes Then
        converterPDF = True
    Else
        converterPDF = False
    End If
    
    ' 5. EXECUTAR FUNÇÃO PRINCIPAL
    Debug.Print "5. Chamando função principal..."
    Call CriarRelatorioFinal(templateWord, pagina, incluirTeste, converterPDF)
    
    Exit Sub
    
ErroHandler:
    Debug.Print "ERRO na macro principal: " & Err.Number & " - " & Err.Description
    MsgBox "❌ ERRO: " & Err.Description & vbCrLf & _
           "Número: " & Err.Number, vbCritical, "Erro no Processamento"
End Sub

' ======================
' FUNÇÃO PRINCIPAL COM CORREÇÕES
' ======================
Sub CriarRelatorioFinal(caminhoWord As String, pagina As Long, _
                       incluirTeste As Boolean, converterPDF As Boolean)
    
    ' Declaração de variáveis
    Dim wordApp As Object, wordDoc As Object
    Dim tabela As Object
    Dim ws As Worksheet
    Dim ultimaLinha As Long, ultimaColuna As Long
    Dim i As Long, j As Long
    Dim caminhoSalvar As String
    Dim sucesso As Boolean
    
    On Error GoTo ErroHandler
    
    ' ========== VALIDAÇÃO INICIAL ==========
    Debug.Print "Validando arquivo Word..."
    If Dir(caminhoWord) = "" Then
        MsgBox "Arquivo Word não encontrado!", vbExclamation
        Exit Sub
    End If
    
    ' ========== OBTER DADOS DA ABA ESPECÍFICA ==========
    Debug.Print "Obtendo dados da aba 'Contingências Duplas'..."
    
    ' Tentar obter a aba específica
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Contingências Duplas")
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets(1) ' Fallback para primeira aba
        MsgBox "Aba 'Contingências Duplas' não encontrada. Usando primeira aba.", vbExclamation
    End If
    On Error GoTo ErroHandler
    
    ultimaLinha = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    ultimaColuna = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    If ultimaLinha < 2 Then
        MsgBox "Não há dados na planilha!", vbExclamation
        Exit Sub
    End If
    
    Debug.Print "Dados: " & ultimaLinha & " linhas, " & ultimaColuna & " colunas"
    
    ' ========== PERGUNTAR ONDE SALVAR ==========
    Debug.Print "Abrindo diálogo para salvar..."
    caminhoSalvar = Application.GetSaveAsFilename( _
        InitialFileName:="Relatorio_Perdas_Duplas_" & Format(Now, "ddmmyyyy_hhmm") & ".docx", _
        FileFilter:="Documentos Word (*.docx), *.docx")
    
    If caminhoSalvar = "False" Then
        Debug.Print "Usuário cancelou salvamento"
        Exit Sub
    End If
    
    ' Garantir extensão .docx
    If LCase(Right(caminhoSalvar, 5)) <> ".docx" Then
        caminhoSalvar = caminhoSalvar & ".docx"
    End If
    
    ' ========== INICIAR WORD ==========
    Debug.Print "Iniciando Word..."
    Set wordApp = CreateObject("Word.Application")
    wordApp.Visible = True ' Deixar visível para debug
    
    ' Abrir template
    Debug.Print "Abrindo documento: " & caminhoWord
    Set wordDoc = wordApp.Documents.Open(caminhoWord)
    
    ' ========== NAVEGAR PARA PÁGINA ESPECÍFICA ==========
    Debug.Print "Navegando para página " & pagina & "..."
    
    ' Método simplificado para ir para página
    wordApp.Selection.GoTo What:=1, Which:=2, Name:=pagina ' wdGoToPage
    
    ' Se não conseguir, adicionar páginas
    If pagina > 1 Then
        ' Vai para o final
        wordApp.Selection.EndKey Unit:=6
        ' Adiciona quebras de página se necessário
        If wordDoc.ComputeStatistics(2) < pagina Then
            For i = wordDoc.ComputeStatistics(2) To pagina - 1
                wordApp.Selection.InsertBreak 7 ' wdPageBreak
            Next i
        End If
    End If
    
    ' ========== INSERIR DADOS PRINCIPAIS ==========
    Debug.Print "Criando tabela principal..."
    
    ' Adicionar título
    wordApp.Selection.TypeText "RELATÓRIO DE PERDAS DUPLAS" & vbCrLf
    wordApp.Selection.TypeText "Gerado em: " & Format(Now, "dd/mm/yyyy HH:MM") & vbCrLf & vbCrLf
    
    ' Criar tabela principal
    Debug.Print "Criando tabela com " & ultimaLinha & "x" & ultimaColuna & " células"
    
    ' Verificar se há seleção ativa
    If wordApp.Selection.Range Is Nothing Then
        ' Se não há seleção, ir para o final
        wordApp.Selection.EndKey Unit:=6
    End If
    
    ' Criar tabela
    On Error Resume Next
    Set tabela = wordDoc.Tables.Add(wordApp.Selection.Range, ultimaLinha, ultimaColuna)
    If Err.Number <> 0 Then
        MsgBox "Erro ao criar tabela: " & Err.Description, vbCritical
        GoTo Limpeza
    End If
    On Error GoTo ErroHandler
    
    ' Tentar aplicar estilo (mas não crítico se falhar)
    On Error Resume Next
    tabela.Style = "Table Grid"
    On Error GoTo ErroHandler
    
    ' ========== CONFIGURAR LARGURAS DAS COLUNAS ==========
    Debug.Print "Configurando larguras das colunas..."
    
    ' Criar dicionário para mapear larguras
    Dim larguras As Object
    Set larguras = CreateObject("Scripting.Dictionary")
    
    ' Definir larguras específicas (em centímetros)
    ' Volume: 3.0 cm (pequeno)
    ' Área Geoelétrica: 6.0 cm (médio)
    ' Contingência Dupla: 10.0 cm (grande)
    ' Horizonte: 4.0 cm (médio)
    
    ' Primeiro, vamos identificar as colunas pelos cabeçalhos
    For j = 1 To ultimaColuna
        Dim cabecalho As String
        cabecalho = Trim(ws.Cells(1, j).Value)
        
        Select Case LCase(cabecalho)
            Case "volume"
                larguras(j) = 2.0  ' 3.0 cm
            Case "área geoelétrica", "area geoeletrica"
                larguras(j) = 6.0  ' 6.0 cm
            Case "contingência dupla", "contingencia dupla"
                larguras(j) = 12.0 ' 10.0 cm
            Case "horizonte"
                larguras(j) = 3.0  ' 4.0 cm
            Case Else
                ' Largura padrão baseada no comprimento do cabeçalho
                Dim comprimento As Integer
                comprimento = Len(cabecalho)
                If comprimento < 10 Then
                    larguras(j) = 3.0
                ElseIf comprimento < 20 Then
                    larguras(j) = 5.0
                Else
                    larguras(j) = 6.0
                End If
        End Select
        
        Debug.Print "Coluna " & j & " (" & cabecalho & "): " & larguras(j) & " cm"
    Next j
    
    ' Aplicar larguras (converter cm para pontos: 1 cm = 28.35 pontos)
    For j = 1 To ultimaColuna
        If larguras.Exists(j) Then
            On Error Resume Next
            tabela.Columns(j).Width = larguras(j) * 28.35
            If Err.Number <> 0 Then
                Debug.Print "Erro ao definir largura da coluna " & j & ": " & Err.Description
                Err.Clear
            End If
            On Error GoTo ErroHandler
        End If
    Next j
    
    ' ========== PREENCHER CABEÇALHO ==========
    Debug.Print "Preenchendo cabeçalho..."
    For j = 1 To ultimaColuna
        Dim cabecalhoTexto As String
        cabecalhoTexto = Trim(ws.Cells(1, j).Value)
        
        tabela.Cell(1, j).Range.Text = cabecalhoTexto
        
        ' Formatar cabeçalho
        On Error Resume Next
        With tabela.Cell(1, j).Range
            .Bold = True
            .Font.Color = RGB(255, 255, 255)  ' Texto branco
            .Shading.BackgroundPatternColor = RGB(68, 114, 196)  ' Fundo azul ONS
            .ParagraphFormat.Alignment = 1  ' Centralizado
            .Font.Size = 10
        End With
        On Error GoTo ErroHandler
    Next j
    
    ' ========== PREENCHER DADOS ==========
    Debug.Print "Preenchendo dados..."
    For i = 2 To ultimaLinha
        For j = 1 To ultimaColuna
            Dim valorCelula As String
            valorCelula = Trim(ws.Cells(i, j).Text)
            
            If valorCelula = "" Then
                valorCelula = "-"
            End If
            
            tabela.Cell(i, j).Range.Text = valorCelula
            
            ' Aplicar formatação condicional para a coluna Horizonte
            Dim cabecalhoColuna As String
            cabecalhoColuna = LCase(Trim(ws.Cells(1, j).Value))
            
            If InStr(cabecalhoColuna, "horizonte") > 0 Then
                Call FormatarHorizonte(tabela.Cell(i, j), valorCelula)
            End If
        Next j
        
        ' Mostrar progresso a cada 10 linhas
        If i Mod 10 = 0 Then
            Debug.Print "Processando linha " & i & " de " & ultimaLinha
            DoEvents
        End If
    Next i
    
    ' ========== APLICAR FORMATAÇÃO GERAL ==========
    Debug.Print "Aplicando formatação geral..."
    
    ' Aplicar bordas
    On Error Resume Next
    With tabela.Borders
        .InsideLineStyle = 1  ' Linha simples
        .OutsideLineStyle = 1  ' Linha simples
    End With
    
    ' Configurar fonte
    With tabela.Range
        .Font.Name = "Calibri"
        .Font.Size = 9
    End With
    
    ' Centralizar verticalmente
    tabela.Rows.VerticalAlignment = 1  ' wdCellAlignVerticalCenter
    
    ' ========== SALVAR ==========
    Debug.Print "Salvando documento..."
    
    ' Verificar se pode salvar
    On Error Resume Next
    wordDoc.SaveAs2 caminhoSalvar
    If Err.Number <> 0 Then
        MsgBox "Erro ao salvar: " & Err.Description, vbCritical
        GoTo Limpeza
    End If
    On Error GoTo ErroHandler
    
    ' ========== CONVERTER PARA PDF ==========
    If converterPDF Then
        Debug.Print "Convertendo para PDF..."
        
        Dim pdfPath As String
        pdfPath = Left(caminhoSalvar, InStrRev(caminhoSalvar, ".")) & "pdf"
        
        On Error Resume Next
        wordDoc.SaveAs2 pdfPath, 17  ' wdFormatPDF
        If Err.Number = 0 Then
            MsgBox "✅ PDF gerado com sucesso!" & vbCrLf & _
                   "Local: " & pdfPath, vbInformation
        Else
            MsgBox "⚠️ Não foi possível converter para PDF automaticamente." & vbCrLf & _
                   "Arquivo Word salvo em: " & caminhoSalvar, vbExclamation
        End If
        On Error GoTo ErroHandler
    End If
    
    ' ========== FINALIZAÇÃO ==========
    sucesso = True
    
    Application.StatusBar = False
    
    MsgBox "✅ Relatório gerado com sucesso!" & vbCrLf & _
           "Arquivo: " & caminhoSalvar, vbInformation, "Concluído"
    
Limpeza:
    ' ========== LIMPEZA DE OBJETOS ==========
    On Error Resume Next
    
    ' Liberar objetos
    If Not larguras Is Nothing Then Set larguras = Nothing
    If Not tabela Is Nothing Then Set tabela = Nothing
    If Not wordDoc Is Nothing Then
        If Not sucesso Then
            wordDoc.Close SaveChanges:=False
        End If
        Set wordDoc = Nothing
    End If
    If Not wordApp Is Nothing Then
        If Not sucesso Then
            wordApp.Quit
        End If
        Set wordApp = Nothing
    End If
    
    Exit Sub
    
ErroHandler:
    Debug.Print "ERRO na linha " & Erl & ": " & Err.Number & " - " & Err.Description
    Debug.Print "Erro Source: " & Err.Source
    
    MsgBox "❌ ERRO DETALHADO:" & vbCrLf & vbCrLf & _
           "Descrição: " & Err.Description & vbCrLf & _
           "Número: " & Err.Number & vbCrLf & _
           "Linha aproximada: " & Erl, vbCritical, "Erro"
    
    Resume Limpeza
End Sub

' ======================
' FUNÇÃO PARA FORMATAR HORIZONTE
' ======================
Private Sub FormatarHorizonte(celula As Object, valor As String)
    On Error Resume Next
    
    Dim horizonte As String
    horizonte = LCase(Trim(valor))
    
    Select Case horizonte
        Case "curto prazo"
            celula.Range.Font.Color = RGB(0, 100, 0)  ' Verde escuro
            celula.Range.Bold = True
            celula.Range.ParagraphFormat.Alignment = 1  ' Centralizado
            
        Case "médio prazo", "medio prazo"
            celula.Range.Font.Color = RGB(255, 140, 0)  ' Laranja
            celula.Range.Bold = True
            celula.Range.ParagraphFormat.Alignment = 1  ' Centralizado
            
        Case "longo prazo"
            celula.Range.Font.Color = RGB(178, 34, 34)  ' Vermelho tijolo
            celula.Range.Bold = True
            celula.Range.ParagraphFormat.Alignment = 1  ' Centralizado
            
        Case Else
            celula.Range.ParagraphFormat.Alignment = 1  ' Centralizado
    End Select
End Sub

' ======================
' FUNÇÃO PARA TESTE RÁPIDO
' ======================
Sub TesteRapido()
    ' Teste rápido para verificar as larguras das colunas
    
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Contingências Duplas")
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets(1)
    End If
    On Error GoTo 0
    
    Dim ultimaColuna As Long
    ultimaColuna = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    Dim msg As String
    msg = "ANÁLISE DAS COLUNAS:" & vbCrLf & vbCrLf
    
    Dim j As Long
    For j = 1 To ultimaColuna
        Dim cabecalho As String
        cabecalho = Trim(ws.Cells(1, j).Value)
        
        msg = msg & "Coluna " & j & ": " & cabecalho & vbCrLf
        
        ' Calcular largura sugerida
        Dim comprimento As Integer
        Dim larguraSugerida As Double
        
        comprimento = Len(cabecalho)
        
        ' Largura baseada no tipo de coluna
        If InStr(LCase(cabecalho), "volume") > 0 Then
            larguraSugerida = 2.0
        ElseIf InStr(LCase(cabecalho), "área") > 0 Or InStr(LCase(cabecalho), "area") > 0 Then
            larguraSugerida = 6.0
        ElseIf InStr(LCase(cabecalho), "contingência") > 0 Or InStr(LCase(cabecalho), "contingencia") > 0 Then
            larguraSugerida = 12.0
        ElseIf InStr(LCase(cabecalho), "horizonte") > 0 Then
            larguraSugerida = 3.0
        Else
            ' Baseado no comprimento
            If comprimento < 10 Then
                larguraSugerida = 3.0
            ElseIf comprimento < 20 Then
                larguraSugerida = 5.0
            Else
                larguraSugerida = 6.0
            End If
        End If
        
        msg = msg & "   Largura sugerida: " & larguraSugerida & " cm" & vbCrLf
        msg = msg & "   (" & larguraSugerida * 28.35 & " pontos no Word)" & vbCrLf & vbCrLf
    Next j
    
    MsgBox msg, vbInformation, "Análise das Colunas"
End Sub

' ======================
' FUNÇÃO PARA VER DADOS
' ======================
Sub VerDados()
    ' Mostra os dados que serão exportados
    
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Contingências Duplas")
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets(1)
    End If
    On Error GoTo 0
    
    Dim ultimaLinha As Long, ultimaColuna As Long
    ultimaLinha = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    ultimaColuna = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    Dim msg As String
    msg = "PRÉ-VISUALIZAÇÃO DOS DADOS:" & vbCrLf & vbCrLf
    msg = msg & "Total de linhas (com cabeçalho): " & ultimaLinha & vbCrLf
    msg = msg & "Total de colunas: " & ultimaColuna & vbCrLf & vbCrLf
    
    ' Mostrar primeiras 5 linhas
    Dim maxLinhas As Long
    maxLinhas = Application.Min(ultimaLinha, 6) ' Cabeçalho + 5 linhas
    
    Dim i As Long, j As Long
    For i = 1 To maxLinhas
        For j = 1 To ultimaColuna
            msg = msg & ws.Cells(i, j).Text & " | "
        Next j
        msg = msg & vbCrLf
    Next i
    
    If ultimaLinha > 6 Then
        msg = msg & vbCrLf & "... mais " & (ultimaLinha - 6) & " linhas"
    End If
    
    MsgBox msg, vbInformation, "Pré-visualização"
End Sub