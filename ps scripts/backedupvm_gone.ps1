#Connect to Azure
Connect-AzAccount
#Set context to correct subscription and tenant
Set-AzContext -Subscription "<SubName>" -Tenant "<TenantID>"

# Define the specific vault name
$vaultName = "<YourVaultName>"
$resourceGroupName = "<YourResourceGroupName>" # Replace <YourResourceGroupName> with the actual resource group name where the vault resides

# Get the specific Recovery Services vault
$vault = Get-AzRecoveryServicesVault -Name $vaultName -ResourceGroupName $resourceGroupName

# Set context to the specified vault
Set-AzRecoveryServicesVaultContext -Vault $vault

# Get all containers in the current vault for Azure VMs
$containers = Get-AzRecoveryServicesBackupContainer -ContainerType "AzureVM" -Status "Registered"

# Get all VMs in the subscription
$allVMs = Get-AzVM

# Initialize a hashtable for VM IDs
$existingVMIds = @{}
foreach ($vm in $allVMs) {
    $existingVMIds[$vm.Id] = $true
}

# Initialize a list to keep track of orphaned backup items
$orphanedBackupItems = @()

foreach ($container in $containers) {
    # Get backup items for each container, specifically looking for Azure VMs
    $backupItems = Get-AzRecoveryServicesBackupItem -Container $container -WorkloadType "AzureVM"

    foreach ($item in $backupItems) {
        if (-not $existingVMIds.ContainsKey($item.SourceResourceId)) {
            # The VM for this backup item does not exist
            # Extracting the VM name from the Name field
            $vmName = ($item.Name -split ';')[-1]
            $orphanDetails = New-Object PSObject -Property @{
                VMName = $vmName
                LastBackupTime = $item.LastBackupTime
            }
            $orphanedBackupItems += $orphanDetails
        }
    }
}

# Output the list of orphaned backup items
$orphanedBackupItems | Format-Table VMName, LastBackupTime

# Export the list to a CSV file with only specified columns
$orphanedBackupItems | Select-Object VMName, LastBackupTime | Export-Csv -Path "./OrphanedBackupItems.csv" -NoTypeInformation