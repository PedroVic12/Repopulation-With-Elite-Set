#! comando de instalação
# Install-Module -Name PnP.PowerShell -Scope CurrentUser -Force -Verbose

#! comando de atualização do powershell
#winget install --id Microsoft.PowerShell --source winget

# Importando o módulo PnP.PowerShell
Import-Module PnP.PowerShell -Force -ErrorAction Stop

Write-Host "Iniciando a conexão com o SharePoint..." -ForegroundColor Cyan
Write-Host "Por padrão, o PowerShell tenta instalar módulos para todos os usuários do sistema, o que exige administrador. Para contornar isso, você deve usar o parâmetro -Scope CurrentUser."



C:\Users\Pedro Victor R V\Documents\programas

# 2. Configure aqui os seus dados
$LinkDaPasta = "https://sharepoint.com..." # Coloque o link completo aqui
$Usuario = "viviane.alvesl@ons.org.br"

# 3. Extrair a URL base do site usando Regex nativo (evita o erro do HttpUtility)
$Uri = [System.Uri]$LinkDaPasta
$UrlBaseSite = "$($Uri.Scheme)://$($Uri.Host)$($Uri.Segments[0])$($Uri.Segments[1])$($Uri.Segments[2])"

# 4. Conectar ao SharePoint pedindo as credenciais
Connect-PnPOnline -Url $UrlBaseSite -Credentials $Usuario

# 5. Identificar o caminho relativo de forma nativa e segura
$CaminhoPasta = $null
if ($Uri.Query -match 'id=([^&]+)') {
    $CaminhoPasta = [System.Uri]::UnescapeDataString($Matches[1])
}

if (-not $CaminhoPasta) {
    $CaminhoPasta = $Uri.AbsolutePath
}

try {
    # 6. Buscar todos os itens dentro da pasta específica
    $Itens = Get-PnPFolderItem -FolderSiteRelativeUrl $CaminhoPasta

    # 7. Filtrar e contar
    $ContagemPastas = 0
    $ContagemArquivos = 0

    foreach ($Item in $Itens) {
        if ($Item.TypedObject -match "Folder") { $ContagemPastas++ }
        if ($Item.TypedObject -match "File") { $ContagemArquivos++ }
    }

    # 8. Retorno dos resultados na tela
    Write-Host "`nConectado com sucesso!" -ForegroundColor Green
    Write-Host "----------------------------------------"
    Write-Host "Pasta analisada: $CaminhoPasta"
    Write-Host "Total de Subpastas: $ContagemPastas"
    Write-Host "Total de Arquivos:  $ContagemArquivos"
    Write-Host "----------------------------------------"
}
catch {
    Write-Error "Erro ao acessar a pasta ou contar os arquivos: $_"
}

# 9. Desconectar ao finalizar
Disconnect-PnPOnline

# ! Comando de execução
# powershell.exe -ExecutionPolicy Bypass -File "C:\Users\viviane.alves\Downloads\CONECTARSHAREPOINT.ps1"
