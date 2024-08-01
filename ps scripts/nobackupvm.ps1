# Function to check and install modules if necessary
function Ensure-Module {
    param (
        [string]$ModuleName
    )

    if (-not (Get-Module -ListAvailable -Name $ModuleName)) {
        Write-Host "Installing module $ModuleName..."
        Install-Module -Name $ModuleName -Force -Scope CurrentUser
    } else {
        Write-Host "Module $ModuleName is already installed."
    }
}

# List of required modules
$requiredModules = @("Az.Accounts", "Az.RecoveryServices", "Az.Compute")

# Ensure each module is installed
foreach ($module in $requiredModules) {
    Ensure-Module -ModuleName $module
}

# Import required modules
foreach ($module in $requiredModules) {
    Import-Module $module
}

# Connect to Azure
Connect-AzAccount

# Set context to correct subscription and tenant
Set-AzContext -Subscription "<Subscription ID>" -Tenant "<Tenant ID>"

# Define the specific vault name
$vaultName = "<VaultName>"
$resourceGroupName = "<YourResourceGroupName>" # Replace <YourResourceGroupName> with the actual resource group name where the vault resides

# Get the specific Recovery Services vault
$vault = Get-AzRecoveryServicesVault -Name $vaultName -ResourceGroupName $resourceGroupName

# Initialize a hashtable to keep track of VMs that are protected
$protectedVMs = @{}

# Set context to the specified vault
Set-AzRecoveryServicesVaultContext -Vault $vault

# Get all containers in the current vault for Azure VMs
$containers = Get-AzRecoveryServicesBackupContainer -ContainerType "AzureVM" -Status "Registered"

foreach ($container in $containers) {
    # Get backup items for each container, specifically looking for Azure VMs
    $backupItems = Get-AzRecoveryServicesBackupItem -Container $container -WorkloadType "AzureVM"

    foreach ($item in $backupItems) {
        # Mark each VM as protected
        $protectedVMs[$item.SourceResourceId] = $true
    }
}

# Get all VMs in the subscription
$allVMs = Get-AzVM

# List VMs that are not in the protected VMs list
$unprotectedVMs = $allVMs | Where-Object { -not $protectedVMs.ContainsKey($_.Id) }

# Output the list of unprotected VMs
$unprotectedVMs | Format-Table Name, ResourceGroupName, Location

# If needed, export the list to a CSV file
$unprotectedVMs | Select-Object Name, ResourceGroupName | Export-Csv -Path "./UnprotectedVMs.csv" -NoTypeInformation