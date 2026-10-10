# Power Automate: Low Stock Alert

## Flow Name: Daily Low Stock Check & Alert

**Type:** Scheduled Cloud Flow  
**Schedule:** Daily at 8:00 AM (configurable)

---

## Flow Definition

### Trigger: Recurrence

**Frequency:** Day  
**Interval:** 1  
**At these hours:** 8  
**Time zone:** (Your local time zone)

---

### Step 1: List Low Stock Items

**Action:** List rows (Dataverse)  
**Table:** Pantry Items  
**Filter rows:** `cr_isactive eq true and cr_currentstock le cr_reorderpoint`  
**Expand Query:** `cr_preferredsupplier($select=cr_name,cr_email)`  
**Order by:** `cr_currentstock asc`

---

### Step 2: Condition - Any Low Stock Items?

**Condition:** `length(outputs('List_Low_Stock_Items')?['body/value'])` is greater than `0`

#### If Yes (Low Stock Items Found):

---

### Step 3: Initialize Variables

**Action:** Initialize variable  
- **varAlertHTML** (String): Empty
- **varCriticalCount** (Integer): 0
- **varOutOfStockCount** (Integer): 0

---

### Step 4: Apply to Each Low Stock Item

**For each:** `outputs('List_Low_Stock_Items')?['body/value']`

#### Step 4a: Determine Severity

**Action:** Compose  
**Expression:**
```
if(equals(items('Apply_to_each')?['cr_currentstock'], 0), 
   'OUT OF STOCK', 
   if(less(items('Apply_to_each')?['cr_currentstock'], 
           div(items('Apply_to_each')?['cr_reorderpoint'], 2)), 
      'CRITICAL', 
      'LOW'))
```

#### Step 4b: Increment Counters

**Action:** Increment variable (for tracking critical and out-of-stock counts)

#### Step 4c: Append to Alert HTML

**Action:** Append to string variable (varAlertHTML)
```html
<tr style="background-color: @{if(equals(outputs('Determine_Severity'), 'OUT OF STOCK'), '#FFE0E0', if(equals(outputs('Determine_Severity'), 'CRITICAL'), '#FFF3E0', '#FFFDE0'))}">
  <td>@{items('Apply_to_each')?['cr_name']}</td>
  <td style="text-align: center;">@{items('Apply_to_each')?['cr_currentstock']}</td>
  <td style="text-align: center;">@{items('Apply_to_each')?['cr_maxstocklevel']}</td>
  <td style="text-align: center;">@{items('Apply_to_each')?['cr_reorderpoint']}</td>
  <td style="text-align: center; font-weight: bold; color: @{if(equals(outputs('Determine_Severity'), 'OUT OF STOCK'), 'red', if(equals(outputs('Determine_Severity'), 'CRITICAL'), '#E65100', '#F57F17'))}">
    @{outputs('Determine_Severity')}
  </td>
  <td>@{items('Apply_to_each')?['cr_preferredsupplier/cr_name']}</td>
</tr>
```

---

### Step 5: Compose Full Alert Email

**Action:** Compose  
**Input:**
```html
<div style="font-family: Arial, sans-serif; max-width: 700px;">

<div style="background-color: #D32F2F; color: white; padding: 15px; text-align: center;">
  <h2 style="margin: 0;">⚠️ Pantry Low Stock Alert</h2>
  <p style="margin: 5px 0 0;">@{formatDateTime(utcNow(), 'MMMM dd, yyyy')}</p>
</div>

<div style="padding: 15px; background-color: #FFF3E0; border-left: 4px solid #FF9800;">
  <p><strong>Summary:</strong> 
    @{variables('varOutOfStockCount')} item(s) out of stock, 
    @{variables('varCriticalCount')} item(s) at critical level,
    @{length(outputs('List_Low_Stock_Items')?['body/value'])} total item(s) need attention.
  </p>
</div>

<table border="1" cellpadding="8" cellspacing="0" 
       style="border-collapse: collapse; width: 100%; margin-top: 15px;">
  <tr style="background-color: #424242; color: white;">
    <th>Item</th>
    <th>Current Stock</th>
    <th>Max Stock</th>
    <th>Reorder Point</th>
    <th>Status</th>
    <th>Supplier</th>
  </tr>
  @{variables('varAlertHTML')}
</table>

<div style="margin-top: 15px; padding: 15px; background-color: #E8F5E9; border-radius: 5px;">
  <p><strong>Action Required:</strong></p>
  <ul>
    <li>Review the items listed above</li>
    <li>Create a supply order in the <a href="[Power Apps URL]">Pantry Supply Manager</a></li>
    <li>Contact suppliers directly for urgent items marked OUT OF STOCK</li>
  </ul>
</div>

</div>
```

---

### Step 6: Send Alert Email

**Action:** Send an email (V2) (Office 365 Outlook)  
**To:** `cafeteriastaff@company.com; officemanager@company.com`  
**Subject:** `⚠️ Pantry Alert: @{length(outputs('List_Low_Stock_Items')?['body/value'])} items need restocking (@{formatDateTime(utcNow(), 'MMM dd')})`  
**Body:** Composed HTML  
**Importance:** High (if any OUT OF STOCK items)

---

### Step 7: Post Teams Notification

**Action:** Post adaptive card in a chat or channel (Microsoft Teams)  
**Post in:** Cafeteria Staff channel  
**Adaptive Card JSON:**
```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "TextBlock",
      "text": "⚠️ Pantry Low Stock Alert",
      "weight": "Bolder",
      "size": "Large",
      "color": "Attention"
    },
    {
      "type": "TextBlock",
      "text": "${itemCount} items need restocking",
      "spacing": "None"
    },
    {
      "type": "FactSet",
      "facts": [
        {
          "title": "Out of Stock:",
          "value": "${outOfStockCount}"
        },
        {
          "title": "Critical:",
          "value": "${criticalCount}"
        },
        {
          "title": "Low:",
          "value": "${lowCount}"
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "Top Priority Items:",
      "weight": "Bolder",
      "spacing": "Medium"
    },
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "items": [
            {
              "type": "TextBlock",
              "text": "Item 1: ${item1Name} (${item1Stock} left)"
            },
            {
              "type": "TextBlock",
              "text": "Item 2: ${item2Name} (${item2Stock} left)"
            },
            {
              "type": "TextBlock",
              "text": "Item 3: ${item3Name} (${item3Stock} left)"
            }
          ]
        }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "Open Pantry Manager",
      "url": "[Power Apps URL]"
    },
    {
      "type": "Action.OpenUrl",
      "title": "Create Order Now",
      "url": "[Power Apps deep link to new order]"
    }
  ]
}
```

---

### Step 8 (Optional): Auto-Create Draft Order

For items that are OUT OF STOCK, automatically create a draft supply order:

**Condition:** `variables('varOutOfStockCount')` is greater than `0`

**If Yes:**
1. Create a new Supply Order (Draft status)
2. For each out-of-stock item, create a line item with quantity = MaxStock - CurrentStock
3. Notify cafeteria staff that a draft order has been prepared

---

## Flow Diagram

```
[Scheduled Trigger: Daily 8:00 AM]
         │
         ▼
[Query Dataverse: Items below reorder point]
         │
         ▼
[Any items found?]
    ┌────┴────┐
   Yes        No
    │         │
    ▼         ▼
[Categorize   [End - No
 each item:    alerts needed]
 Out of Stock
 Critical
 Low]
    │
    ▼
[Build HTML Alert Table]
    │
    ▼
[Send Email to Staff & Manager]
    │
    ▼
[Post Teams Adaptive Card]
    │
    ▼
[Any out of stock?]
    ┌────┴────┐
   Yes        No
    │         │
    ▼         ▼
[Auto-create  [End]
 draft order]
```
