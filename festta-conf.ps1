$buscador = New-Object DirectoryServices.DirectorySearcher
$buscador.Filter = "(&(objectClass=user)(sAMAccountName=$env:USERNAME))"
$ldap_data = $buscador.FindOne()
$ldap = $ldap_data.Properties

$reg_presenca = @{
    matricula = $env:USERNAME
    nome      = $ldap.displayname[0]
    prenome   = $ldap.givenname[0]
    sobrenome = $ldap.sn[0]
    dataNascimento = $ldap.extensionattribute7[0]
    email     = $ldap.extensionattribute5[0]
    hostname  = $env:COMPUTERNAME
    # TODO: Número do PC (Dica: solicitar para o usuário)
}

$json = $reg_presenca | ConvertTo-Json -Depth 5

$dir_conf = Join-Path -Path $HOME -ChildPath ".config\festta"
if (-not (Test-Path -Path $dir_conf)) {
    New-Item -ItemType Directory -Path $dir_conf -Force | Out-Null
}

$arquivo_conf = Join-Path -Path $dir_conf -ChildPath "festta-conf.json"
Set-Content -Path $arquivo_conf -Value $json -Encoding UTF8
