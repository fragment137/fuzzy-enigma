# Connect to your Azure account (if not already connected)
Connect-AzAccount

#Set context to correct subscription and tenant
Set-AzContext -Subscription "<Subscription ID>" -Tenant "<Tenant ID>"

# Get all reservation orders
$reservationOrders = Get-AzReservationOrder

# Filter the reservation orders to include only those with status 'Succeeded' or 'Expiring'
$filteredOrders = $reservationOrders | Where-Object { $_.ProvisioningState -eq 'Succeeded' -or $_.Status -eq 'Expiring' }

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