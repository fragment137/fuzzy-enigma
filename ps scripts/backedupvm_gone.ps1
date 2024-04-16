# Connect to Azure
Connect-AzAccount

# Set context to the correct subscription and tenant
Set-AzContext -Subscription "<INSERT SUBSCRIPTION NAME>" -Tenant "<ENTER TENANT ID>"

# Define the specific vault name and its resource group
$vaultName = "rsv-cae-prd-backup-01"
$resourceGroupName = "rg-cae-prd-bcdr-01" # Replace <YourResourceGroupName> with the actual resource group name where the vault resides

# Get the specific Recovery Services vault
$vault = Get-AzRecoveryServicesVault -Name $vaultName -ResourceGroupName $resourceGroupName

# Set context to the specified vault
Set-AzRecoveryServicesVaultContext -Vault $vault

# Get all containers in the current vault for Azure VMs
$containers = Get-AzRecoveryServicesBackupContainer -ContainerType "AzureVM" -Status "Registered"

# Get all VMs in the subscription
$allVMs = Get-AzVM
$existingVMIds = $allVMs.Id -as [HashSet[string]]

# Initialize a list to keep track of orphaned backup items
$orphanedBackupItems = @()

foreach ($container in $containers) {
    # Get backup items for each container, specifically looking for Azure VMs
    $backupItems = Get-AzRecoveryServicesBackupItem -Container $container -WorkloadType "AzureVM"

    foreach ($item in $backupItems) {
        if (-not $existingVMIds.Contains($item.SourceResourceId)) {
            # The VM for this backup item does not exist
            $orphanedBackupItems += $item
        }
    }
}

# Output the list of orphaned backup items
$orphanedBackupItems | Format-Table Name, ResourceGroupName, ContainerName, LastBackupTime

# If needed, export the list to a CSV file
$orphanedBackupItems | Export-Csv -Path "./OrphanedBackupItems.csv" -NoTypeInformation