# Copilot Agent: Conversation Topics

## Topic 1: Check Stock Level

### Trigger Phrases
- "How many coffee pods are left?"
- "What's the stock level for green tea?"
- "How much milk do we have?"
- "Check inventory for snacks"
- "Are we low on anything?"
- "What's the current stock?"

### Conversation Flow

```
[Trigger: Stock level query detected]
         │
         ▼
[Ask: Which item or category?]
(Skip if already specified in trigger)
         │
         ▼
[Action: Query Dataverse PantryItems]
Filter: cr_name contains '{ItemName}' 
   OR cr_category eq '{Category}'
         │
         ▼
[Condition: Results found?]
    ┌────┴────┐
   Yes        No
    │         │
    ▼         ▼
[Display    [Message: "I couldn't
 results]    find that item. Here
             are our categories:
             Coffee, Snacks,
             Beverages, Condiments"]
```

### Response Template
```
📦 **Stock Level Report**

| Item | Current Stock | Max | Status |
|------|:---:|:---:|--------|
| {ItemName} | {CurrentStock} {Unit} | {MaxStock} | {StockStatus} |

{If low: "⚠️ This item is below the reorder point ({ReorderPoint}). Consider placing an order."}
{If out: "🔴 This item is out of stock! An order should be placed immediately."}
```

### Example Interaction
```
User: "How many coffee pods are left?"

Agent: 📦 **Coffee Pods Stock**

| Item | Current Stock | Max | Status |
|------|:---:|:---:|--------|
| Nespresso Ristretto Pods | 120 pods | 500 | ✅ In Stock |
| Nespresso Lungo Pods | 45 pods | 500 | ⚠️ Low Stock |

⚠️ Lungo Pods are below the reorder point (100). 
Would you like me to show you how to place an order?
```

---

## Topic 2: Last Order Information

### Trigger Phrases
- "When was the last order placed?"
- "When did we last order coffee?"
- "Show me recent orders"
- "What was the last delivery?"
- "Order history for this month"

### Conversation Flow

```
[Trigger: Order history query]
         │
         ▼
[Action: Query SupplyOrders]
Sort: cr_orderdate desc
Top: 5 (or filter by item/date)
         │
         ▼
[Display formatted results]
```

### Response Template
```
📋 **Recent Orders**

**Most Recent Order:**
- Order #: {OrderNumber}
- Date: {OrderDate}
- Status: {Status}
- Total: ${TotalAmount}
- Items: {LineItemSummary}
- {If delivered: "Delivered on: {DeliveryDate}"}

{If more orders: "Would you like to see more order history?"}
```

### Example Interaction
```
User: "When was the last order placed?"

Agent: 📋 **Most Recent Order**

- **Order #:** ORD-00012
- **Date:** October 8, 2026
- **Status:** ✅ Approved
- **Total:** $145.00
- **Items:** Nespresso Ristretto ×50, Sugar ×5, Milk ×10
- **Ordered by:** John Smith

The order before that was ORD-00011 on October 5 ($89.50, Delivered).
Would you like more details on any order?
```

---

## Topic 3: Low Stock Report

### Trigger Phrases
- "Which items are running low?"
- "What do we need to order?"
- "Low stock report"
- "What's running out?"
- "Show me items below reorder point"

### Action
Query PantryItems where `cr_currentstock <= cr_reorderpoint`

### Response Template
```
⚠️ **Low Stock Alert - {Count} items need attention**

🔴 **Out of Stock:**
{List of out-of-stock items, if any}

🟡 **Below Reorder Point:**
| Item | Stock | Reorder At | Suggested Order |
|------|:---:|:---:|:---:|
| {Name} | {Current}/{Max} | {ReorderPoint} | {Max - Current} |

Would you like to create an order for these items?
→ Open [Pantry Supply Manager]({AppLink}) to place an order.
```

---

## Topic 4: Supplier Information

### Trigger Phrases
- "Who supplies our coffee?"
- "What's the supplier contact for snacks?"
- "Supplier details"
- "How long does delivery take from CoffeeWorld?"
- "Give me the email for our coffee supplier"

### Action
Query Suppliers table with category or name filter

### Response Template
```
🏢 **Supplier: {SupplierName}**

- **Contact:** {ContactPerson}
- **Email:** {Email}
- **Phone:** {Phone}
- **Categories:** {Categories}
- **Lead Time:** {LeadTimeDays} business days
- **Contract Expires:** {ContractEndDate}

{If multiple suppliers for category: "We also work with {OtherSupplier} for {Category}."}
```

---

## Topic 5: Order Status

### Trigger Phrases
- "What's the status of my order?"
- "Where is order ORD-00012?"
- "Is my order approved yet?"
- "Track my order"
- "Any pending orders?"

### Action
Query SupplyOrders filtered by current user or order number

### Response Template
```
📦 **Order Status: {OrderNumber}**

- **Status:** {StatusIcon} {StatusText}
- **Submitted:** {OrderDate}
- **Total:** ${TotalAmount}
{If pending approval: "- **Awaiting approval from:** Office Manager"}
{If approved: "- **Approved by:** {ApprovedBy} on {ApprovalDate}"}
{If sent to supplier: "- **Expected delivery:** {ExpectedDelivery}"}
{If rejected: "- **Reason:** {ApprovalComments}"}
```

---

## Topic 6: Spending Report

### Trigger Phrases
- "How much did we spend on snacks this month?"
- "What's our pantry spending this quarter?"
- "Monthly coffee expenses"
- "Budget report for pantry supplies"
- "Total spending on beverages"

### Action
Call Power Automate flow to aggregate SupplyOrders by date range and category

### Response Template
```
💰 **Spending Report: {Period}**

| Category | Amount | Orders |
|----------|-------:|:---:|
| Coffee | ${CoffeeSpend} | {CoffeeOrders} |
| Snacks | ${SnackSpend} | {SnackOrders} |
| Beverages | ${BevSpend} | {BevOrders} |
| Condiments | ${CondSpend} | {CondOrders} |
| **Total** | **${TotalSpend}** | **{TotalOrders}** |

{Comparison: "This is {X%} {more/less} than last {period}."}
```

---

## Topic 7: Place an Order (Redirect)

### Trigger Phrases
- "I want to order more coffee"
- "Can you place an order?"
- "We need to restock"
- "Order supplies"

### Response
```
I can help you get started! To place a supply order:

1. 📱 Open the **Pantry Supply Manager** app → [Open App]({AppLink})
2. Click **New Order**
3. Select items and quantities
4. Submit — orders under $200 and 50 units are auto-approved

Would you like me to check what's currently low in stock first?
```

---

## Topic 8: Help / Capabilities

### Trigger Phrases
- "What can you do?"
- "Help"
- "How do I use this?"

### Response
```
👋 Hi! I'm the **Pantry Supply Assistant**. Here's what I can help with:

📦 **Inventory** — "How many coffee pods are left?"
📋 **Orders** — "When was the last order placed?"
⚠️ **Alerts** — "Which items are running low?"
🏢 **Suppliers** — "Who supplies our snacks?"
📊 **Spending** — "How much did we spend this month?"
🔍 **Status** — "What's the status of my order?"

Just ask me a question in natural language and I'll look it up!
```

---

## Fallback Topic

### When no topic matches:
```
I'm not sure I understand that question. I can help with:
- Checking stock levels
- Order history and status
- Supplier information
- Spending reports

Could you rephrase your question? Or type "help" to see everything I can do.
```

## Escalation Topic

### When user needs human help:
```
I'll connect you with someone who can help further.
Please contact the Office Manager at officemanager@company.com 
or visit the #cafeteria-support channel in Teams.
```
