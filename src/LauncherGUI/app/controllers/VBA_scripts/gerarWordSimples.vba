Sub TestarFuncionamentoBasico()
    On Error GoTo ErroHandler
    
    ' Testar conexão com Word
    Dim wordApp As Object
    Set wordApp = CreateObject("Word.Application")
    wordApp.Visible = True
    
    ' Criar novo documento
    Dim wordDoc As Object
    Set wordDoc = wordApp.Documents.Add
    
    ' Adicionar texto simples
    wordApp.Selection.TypeText "Teste de funcionamento do Word" & vbCrLf
    
    ' Criar tabela simples
    Dim tabela As Object
    Set tabela = wordDoc.Tables.Add(wordApp.Selection.Range, 3, 3)
    
    ' Preencher tabela
    Dim i As Long, j As Long
    For i = 1 To 3
        For j = 1 To 3
            tabela.Cell(i, j).Range.Text = "Célula " & i & "," & j
        Next j
    Next i
    
    ' Salvar
    Dim caminho As String
    caminho = Environ("TEMP") & "\Teste_" & Format(Now, "hhmmss") & ".docx"
    wordDoc.SaveAs2 caminho
    
    MsgBox "✅ Teste concluído com sucesso!" & vbCrLf & _
           "Arquivo salvo em: " & caminho, vbInformation
    
    Exit Sub
    
ErroHandler:
    MsgBox "❌ Erro no teste: " & Err.Description, vbCritical
    On Error Resume Next
    If Not wordDoc Is Nothing Then wordDoc.Close False
    If Not wordApp Is Nothing Then wordApp.Quit
End Sub