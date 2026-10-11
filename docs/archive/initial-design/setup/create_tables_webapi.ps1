# =============================================================================
# Pantry Supply Ordering - Dataverse Web API Setup Script
# =============================================================================
# This script creates all tables, columns, relationships, and choice columns
# using the Dataverse Web API.
#
# Prerequisites:
#   1. Register an Azure AD App with Dynamics CRM permissions
#   2. Update the variables below with your environment URL and app credentials
#   3. Run: .\create_tables_webapi.ps1
# =============================================================================

# --- CONFIGURATION (UPDATE THESE) ---
$envUrl        = "https://YOUR-ORG.crm.dynamics.com"
$tenantId      = "YOUR-TENANT-ID"
$clientId      = "YOUR-APP-CLIENT-ID"
$clientSecret  = "YOUR-APP-CLIENT-SECRET"
$publisherPrefix = "cr"

# --- AUTHENTICATE ---
Write-Host "Authenticating to Dataverse..." -ForegroundColor Cyan
$tokenBody = @{
    grant_type    = "client_credentials"
    client_id     = $clientId
    client_secret = $clientSecret
    resource      = $envUrl
}
$tokenResponse = Invoke-RestMethod -Method Post -Uri "https://login.microsoftonline.com/$tenantId/oauth2/token" -Body $tokenBody
$headers = @{
    "Authorization" = "Bearer $($tokenResponse.access_token)"
    "OData-MaxVersion" = "4.0"
    "OData-Version" = "4.0"
    "Accept" = "application/json"
    "Content-Type" = "application/json; charset=utf-8"
    "Prefer" = "return=representation"
}
$apiUrl = "$envUrl/api/data/v9.2"
Write-Host "Authenticated successfully." -ForegroundColor Green

# --- HELPER FUNCTIONS ---
function New-GlobalOptionSet {
    param($Name, $DisplayName, $Options)
    $optionItems = @()
    foreach ($opt in $Options) {
        $optionItems += @{
            Value = $opt.Value
            Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = $opt.Label; LanguageCode = 1033 }) }
        }
    }
    $body = @{
        "@odata.type" = "#Microsoft.Dynamics.CRM.OptionSetMetadata"
        Name = $Name
        DisplayName = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = $DisplayName; LanguageCode = 1033 }) }
        IsGlobal = $true
        OptionSetType = "Picklist"
        Options = $optionItems
    } | ConvertTo-Json -Depth 10
    try {
        Invoke-RestMethod -Method Post -Uri "$apiUrl/GlobalOptionSetDefinitions" -Headers $headers -Body $body | Out-Null
        Write-Host "  Created option set: $DisplayName" -ForegroundColor Green
    } catch {
        Write-Host "  Option set '$DisplayName' may already exist: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function New-Entity {
    param($SchemaName, $DisplayName, $PluralName, $Description, $OwnershipType, $PrimaryColumnName, $PrimaryColumnMaxLength)
    $body = @{
        "@odata.type" = "#Microsoft.Dynamics.CRM.EntityMetadata"
        SchemaName = $SchemaName
        DisplayName = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = $DisplayName; LanguageCode = 1033 }) }
        DisplayCollectionName = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = $PluralName; LanguageCode = 1033 }) }
        Description = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = $Description; LanguageCode = 1033 }) }
        OwnershipType = $OwnershipType
        IsActivity = $false
        HasNotes = $true
        HasActivities = $false
        PrimaryNameAttribute = "${SchemaName.ToLower()}_name"  # not used directly
        Attributes = @(
            @{
                "@odata.type" = "#Microsoft.Dynamics.CRM.StringAttributeMetadata"
                SchemaName = "${publisherPrefix}_name"
                DisplayName = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = $PrimaryColumnName; LanguageCode = 1033 }) }
                IsPrimaryName = $true
                RequiredLevel = @{ Value = "ApplicationRequired" }
                MaxLength = $PrimaryColumnMaxLength
            }
        )
    } | ConvertTo-Json -Depth 10
    try {
        $result = Invoke-RestMethod -Method Post -Uri "$apiUrl/EntityDefinitions" -Headers $headers -Body $body
        Write-Host "  Created table: $DisplayName" -ForegroundColor Green
        return $result.MetadataId
    } catch {
        Write-Host "  Table '$DisplayName' creation failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function New-Column {
    param($EntityLogicalName, $SchemaName, $DisplayName, $Type, $Properties)
    $body = $Properties
    $body["SchemaName"] = $SchemaName
    $body["DisplayName"] = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = $DisplayName; LanguageCode = 1033 }) }
    $jsonBody = $body | ConvertTo-Json -Depth 10
    try {
        Invoke-RestMethod -Method Post -Uri "$apiUrl/EntityDefinitions(LogicalName='$EntityLogicalName')/Attributes" -Headers $headers -Body $jsonBody | Out-Null
        Write-Host "    Added column: $DisplayName" -ForegroundColor Gray
    } catch {
        Write-Host "    Column '$DisplayName' failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# =============================================================================
# STEP 1: CREATE GLOBAL OPTION SETS
# =============================================================================
Write-Host "`nStep 1: Creating Global Option Sets..." -ForegroundColor Cyan

New-GlobalOptionSet -Name "${publisherPrefix}_itemcategory" -DisplayName "Item Category" -Options @(
    @{Value=100000000; Label="Coffee"}, @{Value=100000001; Label="Snacks"},
    @{Value=100000002; Label="Beverages"}, @{Value=100000003; Label="Condiments"},
    @{Value=100000004; Label="Cleaning Supplies"}, @{Value=100000005; Label="Other"}
)

New-GlobalOptionSet -Name "${publisherPrefix}_itemunit" -DisplayName "Item Unit" -Options @(
    @{Value=100000000; Label="Pods"}, @{Value=100000001; Label="Packets"},
    @{Value=100000002; Label="Boxes"}, @{Value=100000003; Label="Bottles"},
    @{Value=100000004; Label="Units"}
)

New-GlobalOptionSet -Name "${publisherPrefix}_orderstatus" -DisplayName "Order Status" -Options @(
    @{Value=100000000; Label="Draft"}, @{Value=100000001; Label="Submitted"},
    @{Value=100000002; Label="Pending Approval"}, @{Value=100000003; Label="Approved"},
    @{Value=100000004; Label="Rejected"}, @{Value=100000005; Label="Sent to Supplier"},
    @{Value=100000006; Label="Delivered"}, @{Value=100000007; Label="Cancelled"}
)

New-GlobalOptionSet -Name "${publisherPrefix}_approvalstatus" -DisplayName "Approval Status" -Options @(
    @{Value=100000000; Label="Pending"}, @{Value=100000001; Label="Approved"},
    @{Value=100000002; Label="Rejected"}
)

New-GlobalOptionSet -Name "${publisherPrefix}_approvalaction" -DisplayName "Approval Action" -Options @(
    @{Value=100000000; Label="Submitted"}, @{Value=100000001; Label="Approved"},
    @{Value=100000002; Label="Rejected"}, @{Value=100000003; Label="Escalated"}
)

New-GlobalOptionSet -Name "${publisherPrefix}_suppliercategory" -DisplayName "Supplier Category" -Options @(
    @{Value=100000000; Label="Coffee"}, @{Value=100000001; Label="Snacks"},
    @{Value=100000002; Label="Beverages"}, @{Value=100000003; Label="General"}
)

# =============================================================================
# STEP 2: CREATE TABLES
# =============================================================================
Write-Host "`nStep 2: Creating Tables..." -ForegroundColor Cyan

Write-Host "`n  Creating Supplier table..."
New-Entity -SchemaName "${publisherPrefix}_supplier" -DisplayName "Supplier" -PluralName "Suppliers" `
    -Description "Supplier contact information" -OwnershipType "OrganizationOwned" `
    -PrimaryColumnName "Supplier Name" -PrimaryColumnMaxLength 200

Write-Host "`n  Creating Pantry Item table..."
New-Entity -SchemaName "${publisherPrefix}_pantryitem" -DisplayName "Pantry Item" -PluralName "Pantry Items" `
    -Description "Inventory catalog of pantry supplies" -OwnershipType "OrganizationOwned" `
    -PrimaryColumnName "Item Name" -PrimaryColumnMaxLength 100

Write-Host "`n  Creating Supply Order table..."
New-Entity -SchemaName "${publisherPrefix}_supplyorder" -DisplayName "Supply Order" -PluralName "Supply Orders" `
    -Description "Supply order requests" -OwnershipType "UserOwned" `
    -PrimaryColumnName "Order Number" -PrimaryColumnMaxLength 20

Write-Host "`n  Creating Order Line Item table..."
New-Entity -SchemaName "${publisherPrefix}_orderlineitem" -DisplayName "Order Line Item" -PluralName "Order Line Items" `
    -Description "Individual items in a supply order" -OwnershipType "OrganizationOwned" `
    -PrimaryColumnName "Line Item" -PrimaryColumnMaxLength 100

Write-Host "`n  Creating Approval History table..."
New-Entity -SchemaName "${publisherPrefix}_approvalhistory" -DisplayName "Approval History" -PluralName "Approval History" `
    -Description "Audit trail for approval decisions" -OwnershipType "OrganizationOwned" `
    -PrimaryColumnName "Record" -PrimaryColumnMaxLength 100

# =============================================================================
# STEP 3: ADD COLUMNS TO TABLES
# =============================================================================
Write-Host "`nStep 3: Adding columns to tables..." -ForegroundColor Cyan

# --- Supplier columns ---
Write-Host "`n  Supplier columns:"
New-Column -EntityLogicalName "${publisherPrefix}_supplier" -SchemaName "${publisherPrefix}_contactperson" -DisplayName "Contact Person" -Type "String" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.StringAttributeMetadata"; MaxLength = 100
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplier" -SchemaName "${publisherPrefix}_email" -DisplayName "Email" -Type "String" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.StringAttributeMetadata"; MaxLength = 200; FormatName = @{ Value = "Email" }
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplier" -SchemaName "${publisherPrefix}_phone" -DisplayName "Phone" -Type "String" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.StringAttributeMetadata"; MaxLength = 50; FormatName = @{ Value = "Phone" }
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplier" -SchemaName "${publisherPrefix}_address" -DisplayName "Address" -Type "Memo" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MemoAttributeMetadata"; MaxLength = 2000
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplier" -SchemaName "${publisherPrefix}_leadtimedays" -DisplayName "Lead Time (Days)" -Type "Integer" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.IntegerAttributeMetadata"; MinValue = 0; MaxValue = 365
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplier" -SchemaName "${publisherPrefix}_isactive" -DisplayName "Is Active" -Type "Boolean" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.BooleanAttributeMetadata"; DefaultValue = $true
    RequiredLevel = @{ Value = "ApplicationRequired" }
    OptionSet = @{
        TrueOption = @{ Value = 1; Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = "Yes"; LanguageCode = 1033 }) } }
        FalseOption = @{ Value = 0; Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = "No"; LanguageCode = 1033 }) } }
    }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplier" -SchemaName "${publisherPrefix}_contractenddate" -DisplayName "Contract End Date" -Type "DateTime" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"; Format = "DateOnly"; DateTimeBehavior = @{ Value = "UserLocal" }
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplier" -SchemaName "${publisherPrefix}_notes" -DisplayName "Notes" -Type "Memo" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MemoAttributeMetadata"; MaxLength = 4000
    RequiredLevel = @{ Value = "None" }
}

# --- Pantry Item columns ---
Write-Host "`n  Pantry Item columns:"
New-Column -EntityLogicalName "${publisherPrefix}_pantryitem" -SchemaName "${publisherPrefix}_currentstock" -DisplayName "Current Stock" -Type "Integer" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.IntegerAttributeMetadata"; MinValue = 0; MaxValue = 999999
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_pantryitem" -SchemaName "${publisherPrefix}_maxstocklevel" -DisplayName "Max Stock Level" -Type "Integer" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.IntegerAttributeMetadata"; MinValue = 1; MaxValue = 999999
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_pantryitem" -SchemaName "${publisherPrefix}_reorderpoint" -DisplayName "Reorder Point" -Type "Integer" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.IntegerAttributeMetadata"; MinValue = 0; MaxValue = 999999
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_pantryitem" -SchemaName "${publisherPrefix}_unitprice" -DisplayName "Unit Price" -Type "Money" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MoneyAttributeMetadata"; PrecisionSource = 2
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_pantryitem" -SchemaName "${publisherPrefix}_isactive" -DisplayName "Is Active" -Type "Boolean" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.BooleanAttributeMetadata"; DefaultValue = $true
    RequiredLevel = @{ Value = "ApplicationRequired" }
    OptionSet = @{
        TrueOption = @{ Value = 1; Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = "Yes"; LanguageCode = 1033 }) } }
        FalseOption = @{ Value = 0; Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = "No"; LanguageCode = 1033 }) } }
    }
}
New-Column -EntityLogicalName "${publisherPrefix}_pantryitem" -SchemaName "${publisherPrefix}_lastordereddate" -DisplayName "Last Ordered Date" -Type "DateTime" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"; Format = "DateOnly"; DateTimeBehavior = @{ Value = "UserLocal" }
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_pantryitem" -SchemaName "${publisherPrefix}_lastrestockeddate" -DisplayName "Last Restocked Date" -Type "DateTime" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"; Format = "DateOnly"; DateTimeBehavior = @{ Value = "UserLocal" }
    RequiredLevel = @{ Value = "None" }
}

# --- Supply Order columns ---
Write-Host "`n  Supply Order columns:"
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_orderdate" -DisplayName "Order Date" -Type "DateTime" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"; Format = "DateAndTime"; DateTimeBehavior = @{ Value = "UserLocal" }
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_totalamount" -DisplayName "Total Amount" -Type "Money" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MoneyAttributeMetadata"; PrecisionSource = 2
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_totalquantity" -DisplayName "Total Quantity" -Type "Integer" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.IntegerAttributeMetadata"; MinValue = 0; MaxValue = 999999
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_requiresapproval" -DisplayName "Requires Approval" -Type "Boolean" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.BooleanAttributeMetadata"; DefaultValue = $false
    RequiredLevel = @{ Value = "ApplicationRequired" }
    OptionSet = @{
        TrueOption = @{ Value = 1; Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = "Yes"; LanguageCode = 1033 }) } }
        FalseOption = @{ Value = 0; Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = "No"; LanguageCode = 1033 }) } }
    }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_supplieremailsent" -DisplayName "Supplier Email Sent" -Type "Boolean" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.BooleanAttributeMetadata"; DefaultValue = $false
    RequiredLevel = @{ Value = "ApplicationRequired" }
    OptionSet = @{
        TrueOption = @{ Value = 1; Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = "Yes"; LanguageCode = 1033 }) } }
        FalseOption = @{ Value = 0; Label = @{ "@odata.type" = "#Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ Label = "No"; LanguageCode = 1033 }) } }
    }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_approvaldate" -DisplayName "Approval Date" -Type "DateTime" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"; Format = "DateAndTime"; DateTimeBehavior = @{ Value = "UserLocal" }
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_approvalcomments" -DisplayName "Approval Comments" -Type "Memo" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MemoAttributeMetadata"; MaxLength = 4000
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_expecteddelivery" -DisplayName "Expected Delivery" -Type "DateTime" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"; Format = "DateOnly"; DateTimeBehavior = @{ Value = "UserLocal" }
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_deliverydate" -DisplayName "Delivery Date" -Type "DateTime" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"; Format = "DateOnly"; DateTimeBehavior = @{ Value = "UserLocal" }
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_supplyorder" -SchemaName "${publisherPrefix}_notes" -DisplayName "Notes" -Type "Memo" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MemoAttributeMetadata"; MaxLength = 4000
    RequiredLevel = @{ Value = "None" }
}

# --- Order Line Item columns ---
Write-Host "`n  Order Line Item columns:"
New-Column -EntityLogicalName "${publisherPrefix}_orderlineitem" -SchemaName "${publisherPrefix}_quantity" -DisplayName "Quantity" -Type "Integer" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.IntegerAttributeMetadata"; MinValue = 1; MaxValue = 999999
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_orderlineitem" -SchemaName "${publisherPrefix}_unitprice" -DisplayName "Unit Price" -Type "Money" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MoneyAttributeMetadata"; PrecisionSource = 2
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_orderlineitem" -SchemaName "${publisherPrefix}_linetotal" -DisplayName "Line Total" -Type "Money" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MoneyAttributeMetadata"; PrecisionSource = 2
    RequiredLevel = @{ Value = "None" }
}
New-Column -EntityLogicalName "${publisherPrefix}_orderlineitem" -SchemaName "${publisherPrefix}_currentstockatorder" -DisplayName "Current Stock at Order" -Type "Integer" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.IntegerAttributeMetadata"; MinValue = 0; MaxValue = 999999
    RequiredLevel = @{ Value = "None" }
}

# --- Approval History columns ---
Write-Host "`n  Approval History columns:"
New-Column -EntityLogicalName "${publisherPrefix}_approvalhistory" -SchemaName "${publisherPrefix}_actiondate" -DisplayName "Action Date" -Type "DateTime" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"; Format = "DateAndTime"; DateTimeBehavior = @{ Value = "UserLocal" }
    RequiredLevel = @{ Value = "ApplicationRequired" }
}
New-Column -EntityLogicalName "${publisherPrefix}_approvalhistory" -SchemaName "${publisherPrefix}_comments" -DisplayName "Comments" -Type "Memo" -Properties @{
    "@odata.type" = "#Microsoft.Dynamics.CRM.MemoAttributeMetadata"; MaxLength = 4000
    RequiredLevel = @{ Value = "None" }
}

# =============================================================================
# Note: Picklist columns referencing global option sets, lookup columns for
# relationships, and multi-select picklists require additional API calls
# with specific relationship metadata. See manual-setup-steps.md for those.
# =============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Tables and basic columns created." -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "REMAINING MANUAL STEPS:" -ForegroundColor Yellow
Write-Host "1. Add Choice columns (Category, Unit, Status) to tables" -ForegroundColor Yellow
Write-Host "2. Add Lookup relationships between tables" -ForegroundColor Yellow
Write-Host "3. Set Autonumber on Order Number and Approval Record" -ForegroundColor Yellow
Write-Host "4. Create Cloud Flows (see power-automate/ docs)" -ForegroundColor Yellow
Write-Host "5. Build Canvas App (see power-apps/ docs)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
