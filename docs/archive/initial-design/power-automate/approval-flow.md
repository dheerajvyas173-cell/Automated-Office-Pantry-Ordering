# Power Automate: Order Approval Workflow

## Flow Name: Pantry Order Approval

**Type:** Automated Cloud Flow  
**Trigger:** When a row is added or modified (Dataverse)

---

## Flow Definition

### Trigger: When a Supply Order is Created or Updated

**Connector:** Microsoft Dataverse  
**Action:** When a row is added, modified or deleted  
**Table:** Supply Orders  
**Change type:** Added or Modified  
**Scope:** Organization  
**Filter rows:** `cr_orderstatus eq 3` (Pending Approval)

---

### Step 1: Get Order Details

**Action:** Get a row by ID (Dataverse)  
**Table:** Supply Orders  
**Row ID:** `triggerBody()?['cr_supplyorderid']`  
**Expand Query:** `cr_requestedby($select=fullname,internalemailaddress)`

---

### Step 2: List Order Line Items

**Action:** List rows (Dataverse)  
**Table:** Order Line Items  
**Filter rows:** `_cr_order_value eq '@{triggerBody()?['cr_supplyorderid']}'`  
**Expand Query:** `cr_pantryitem($select=cr_name,cr_unit,cr_unitprice)`

---

### Step 3: Compose Order Summary HTML

**Action:** Compose  
**Input:**
```html
<h2>Pantry Supply Order Approval Request</h2>

<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; font-family: Arial;">
  <tr style="background-color: #4472C4; color: white;">
    <th>Order Number</th>
    <th>Requested By</th>
    <th>Order Date</th>
    <th>Total Amount</th>
    <th>Total Quantity</th>
  </tr>
  <tr>
    <td>@{outputs('Get_Order_Details')?['body/cr_ordernumber']}</td>
    <td>@{outputs('Get_Order_Details')?['body/cr_requestedby/fullname']}</td>
    <td>@{formatDateTime(outputs('Get_Order_Details')?['body/cr_orderdate'], 'MMMM dd, yyyy')}</td>
    <td>$@{outputs('Get_Order_Details')?['body/cr_totalamount']}</td>
    <td>@{outputs('Get_Order_Details')?['body/cr_totalquantity']}</td>
  </tr>
</table>

<h3>Order Items:</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; font-family: Arial;">
  <tr style="background-color: #5B9BD5; color: white;">
    <th>Item</th>
    <th>Quantity</th>
    <th>Unit Price</th>
    <th>Line Total</th>
  </tr>
  <!-- Apply to each line item -->
</table>

<p><strong>Notes:</strong> @{outputs('Get_Order_Details')?['body/cr_notes']}</p>
<p><strong>Reason for Approval:</strong> 
@{if(greater(outputs('Get_Order_Details')?['body/cr_totalamount'], 200), 'Order exceeds $200 budget threshold. ', '')}
@{if(greater(outputs('Get_Order_Details')?['body/cr_totalquantity'], 50), 'Order exceeds 50-unit quantity threshold.', '')}
</p>
```

---

### Step 4: Start and Wait for an Approval

**Action:** Start and wait for an approval (Approvals)  
**Approval type:** Approve/Reject - First to respond  
**Title:** `Pantry Order Approval: @{outputs('Get_Order_Details')?['body/cr_ordernumber']} - $@{outputs('Get_Order_Details')?['body/cr_totalamount']}`  
**Assigned to:** `officemanager@company.com` (configure with your manager's email)  
**Details:** `@{outputs('Compose_Order_Summary')}`  
**Item link:** Link to the order in Power Apps  
**Item link description:** `View in Pantry Manager App`

---

### Step 5: Condition - Check Approval Response

**Condition:** `outputs('Start_and_wait_for_an_approval')?['body/outcome']` is equal to `Approve`

#### If Yes (Approved):

##### Step 5a: Update Order - Approved
**Action:** Update a row (Dataverse)  
**Table:** Supply Orders  
**Row ID:** `triggerBody()?['cr_supplyorderid']`  
**Values:**
- Order Status: `4` (Approved)
- Approval Status: `2` (Approved)
- Approved By: Approver's ID
- Approval Date: `utcNow()`
- Approval Comments: `outputs('Start_and_wait_for_an_approval')?['body/responses'][0]['comments']`

##### Step 5b: Create Approval History Record
**Action:** Add a new row (Dataverse)  
**Table:** Approval History  
**Values:**
- Order: Order ID
- Action: `2` (Approved)
- Action By: Approver
- Action Date: `utcNow()`
- Comments: Approver's comments

##### Step 5c: Send Approval Notification to Requester
**Action:** Send an email (V2) (Office 365 Outlook)  
**To:** Requester's email  
**Subject:** `✅ Your pantry order @{outputs('Get_Order_Details')?['body/cr_ordernumber']} has been approved`  
**Body:**
```html
<p>Hi @{outputs('Get_Order_Details')?['body/cr_requestedby/fullname']},</p>
<p>Your pantry supply order <strong>@{outputs('Get_Order_Details')?['body/cr_ordernumber']}</strong> 
for <strong>$@{outputs('Get_Order_Details')?['body/cr_totalamount']}</strong> has been 
<span style="color: green; font-weight: bold;">APPROVED</span>.</p>
<p>The order will now be sent to the supplier automatically.</p>
<p><strong>Approver Comments:</strong> @{outputs('Start_and_wait_for_an_approval')?['body/responses'][0]['comments']}</p>
```

##### Step 5d: Trigger Supplier Email (call child flow or continue inline)
*See [supplier-order-flow.md](supplier-order-flow.md) for the supplier email flow.*

#### If No (Rejected):

##### Step 5e: Update Order - Rejected
**Action:** Update a row (Dataverse)  
**Table:** Supply Orders  
**Row ID:** `triggerBody()?['cr_supplyorderid']`  
**Values:**
- Order Status: `5` (Rejected)
- Approval Status: `3` (Rejected)
- Approved By: Rejector's ID
- Approval Date: `utcNow()`
- Approval Comments: Rejector's comments

##### Step 5f: Create Rejection History Record
**Action:** Add a new row (Dataverse)  
**Table:** Approval History

##### Step 5g: Send Rejection Notification
**Action:** Send an email (V2) (Office 365 Outlook)  
**To:** Requester's email  
**Subject:** `❌ Your pantry order @{outputs('Get_Order_Details')?['body/cr_ordernumber']} was not approved`  
**Body:**
```html
<p>Hi @{outputs('Get_Order_Details')?['body/cr_requestedby/fullname']},</p>
<p>Your pantry supply order <strong>@{outputs('Get_Order_Details')?['body/cr_ordernumber']}</strong> 
for <strong>$@{outputs('Get_Order_Details')?['body/cr_totalamount']}</strong> has been 
<span style="color: red; font-weight: bold;">REJECTED</span>.</p>
<p><strong>Reason:</strong> @{outputs('Start_and_wait_for_an_approval')?['body/responses'][0]['comments']}</p>
<p>You can modify and resubmit the order from the Pantry Supply Manager app.</p>
```

---

## Flow Diagram

```
[Trigger: Order Pending Approval]
         │
         ▼
[Get Order Details]
         │
         ▼
[List Line Items]
         │
         ▼
[Compose HTML Summary]
         │
         ▼
[Start Approval Request]
         │
    ┌────┴────┐
    │         │
 Approved  Rejected
    │         │
    ▼         ▼
[Update    [Update
 Order]     Order]
    │         │
    ▼         ▼
[Log       [Log
 History]   History]
    │         │
    ▼         ▼
[Notify    [Notify
 Requester] Requester]
    │
    ▼
[Trigger Supplier
 Email Flow]
```

---

## Error Handling

### Configured After Run Settings

- **Get Order Details**: If fails → Send error notification to admin
- **Start Approval**: If times out (72 hours) → Auto-escalate to backup approver
- **Update Order**: If fails → Retry up to 3 times, then notify admin
- **Send Email**: If fails → Log to error table, retry once

### Timeout Configuration

The approval step has a **72-hour timeout**. If no response is received:
1. The order is escalated to a backup approver
2. A reminder is sent to the original approver
3. After an additional 24 hours, the order is auto-approved with a note
