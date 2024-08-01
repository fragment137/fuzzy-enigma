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
$requiredModules = @("Az.Accounts", "Az.Reservations", "Az.Resources")

# Ensure each module is installed
foreach ($module in $requiredModules) {
    Ensure-Module -ModuleName $module
}

# Import required modules
foreach ($module in $requiredModules) {
    Import-Module $module
}

# Connect to your Azure account (if not already connected)
Connect-AzAccount

# Set context to correct subscription and tenant
Set-AzContext -Subscription "<Subscription ID>" -Tenant "<Tenant ID>"

# Get all reservation orders
$reservationOrders = Get-AzReservationOrder

# Filter the reservation orders to include only those with status 'Succeeded'
$filteredOrders = $reservationOrders | Where-Object { $_.ProvisioningState -eq 'Succeeded' }

# Define the user and role to be assigned
$userEmail = "<User Email>"
$userId = $(Get-AzADUser -UserPrincipalName $userEmail).Id
$roleDefinitionName = "Owner"

# Loop through each filtered reservation order and add the user as an owner
foreach ($order in $filteredOrders) {
    $orderId = $order.Id
    New-AzRoleAssignment -ObjectId $userId -RoleDefinitionName $roleDefinitionName -Scope $orderid
}

# Display the filtered reservation orders
$filteredOrders