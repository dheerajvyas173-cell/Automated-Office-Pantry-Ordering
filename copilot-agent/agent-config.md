# Copilot Studio Agent Configuration

## Agent Name: Pantry Supply Assistant

**Platform:** Microsoft Copilot Studio  
**Type:** Custom Agent  
**Channel:** Microsoft Teams (primary), Power Apps (embedded)

---

## Agent Setup

### Step 1: Create the Agent

1. Go to [Copilot Studio](https://copilotstudio.microsoft.com)
2. Select your environment (same as Dataverse tables)
3. Click **Create** → **New agent**
4. Name: **Pantry Supply Assistant**
5. Description: "AI assistant for office pantry inventory, orders, and supplier information"
6. Primary language: English

### Step 2: Configure Agent Instructions

In the **Instructions** section, set the agent's system prompt:

```
You are the Pantry Supply Assistant for our office. You help employees and 
cafeteria staff with:

1. Checking current stock levels for pantry items (coffee, snacks, beverages, condiments)
2. Finding out when items were last ordered or restocked
3. Providing supplier contact information and lead times
4. Identifying which items are running low or out of stock
5. Sharing order history and spending information
6. Helping users understand the ordering process

Always provide specific numbers and dates when available. If you don't have 
enough information to answer a question, suggest the user check the Pantry 
Supply Manager app.

Be concise, friendly, and professional. Format responses with clear structure 
when listing multiple items.
```

### Step 3: Add Knowledge Sources

#### Dataverse Tables (Primary Knowledge)

Add the following Dataverse tables as knowledge sources:

1. **Pantry Items** (`cr_pantryitem`)
   - Allows queries about stock levels, item categories, pricing
   - Key columns: Name, Category, CurrentStock, MaxStock, ReorderPoint, Unit, UnitPrice

2. **Supply Orders** (`cr_supplyorder`)
   - Allows queries about order history, status, spending
   - Key columns: OrderNumber, OrderDate, OrderStatus, TotalAmount, RequestedBy

3. **Order Line Items** (`cr_orderlineitem`)
   - Provides detail on what was ordered
   - Key columns: PantryItem, Quantity, UnitPrice, LineTotal

4. **Suppliers** (`cr_supplier`)
   - Supplier contact info and lead times
   - Key columns: Name, ContactPerson, Email, Phone, Category, LeadTimeDays

#### Configuration for Each Table:
- **Access:** Read-only
- **Description:** Provide a clear description so the agent understands context
- **Synonyms:** Map common terms (e.g., "coffee pods" → "Nespresso Original Pods")

### Step 4: Configure Authentication

- **Authentication:** Authenticate with Microsoft
- **Require sign-in:** Yes
- **Service Provider:** Azure Active Directory v2
- Ensures users only see data they're authorized to access

---

## Agent Topics

See [topics.md](topics.md) for detailed topic definitions.

### Topic Overview

| Topic | Trigger Phrases | Action |
|-------|----------------|--------|
| Check Stock Level | "how many", "stock level", "how much", "left" | Query PantryItems table |
| Low Stock Report | "running low", "need to order", "low stock" | Filter items ≤ reorder point |
| Last Order Info | "last order", "when was", "ordered" | Query SupplyOrders (most recent) |
| Supplier Info | "supplier", "vendor", "contact", "who supplies" | Query Suppliers table |
| Order Status | "order status", "where is my order", "tracking" | Query SupplyOrders by user |
| Spending Report | "how much spent", "spending", "budget", "cost" | Aggregate SupplyOrders amounts |
| Place Order | "order", "restock", "need more" | Direct user to Power Apps |
| Help | "help", "what can you do" | Show capabilities |

---

## Power Automate Cloud Flow Actions

For queries that need computed results, the agent calls Power Automate flows:

### Flow 1: Get Stock Summary
**Trigger:** HTTP Request (from Copilot)  
**Input:** Category (optional)  
**Process:**
1. Query PantryItems from Dataverse
2. Calculate totals by category
3. Identify items below reorder point  

**Returns:**
```json
{
  "totalItems": 15,
  "lowStockItems": 3,
  "outOfStockItems": 0,
  "categories": [
    {
      "name": "Coffee",
      "items": [
        {"name": "Nespresso Ristretto", "stock": 120, "max": 500, "status": "In Stock"},
        {"name": "Nespresso Lungo", "stock": 45, "max": 500, "status": "Low Stock"}
      ]
    }
  ]
}
```

### Flow 2: Get Order History
**Trigger:** HTTP Request (from Copilot)  
**Input:** DateRange, Category (optional)  
**Process:**
1. Query SupplyOrders within date range
2. Join with OrderLineItems for details
3. Calculate totals

**Returns:** Order summary with dates, amounts, items

### Flow 3: Get Supplier Details
**Trigger:** HTTP Request (from Copilot)  
**Input:** Category or SupplierName  
**Process:** Query Suppliers table with filters

**Returns:** Supplier contact info, lead times, categories

---

## Teams Channel Integration

### Deployment to Teams
1. In Copilot Studio → **Channels** → **Microsoft Teams**
2. Click **Turn on Teams**
3. Configure availability:
   - **Show in Teams app store**: Yes
   - **Add to specific teams/channels**: Cafeteria Staff channel
4. Customize:
   - Icon: Coffee cup or pantry icon
   - Short description: "Ask about pantry stock, orders, and suppliers"
   - Long description: Full capability list

### Power Apps Embedding
1. In Power Apps Canvas app, add a **Chatbot** control
2. Set the **Bot** property to your Copilot agent
3. Position in bottom-right corner as a floating widget
4. Users can ask questions without leaving the app

---

## Generative AI Settings

### Generative Answers
- **Enabled:** Yes
- **Content moderation:** Medium
- **Data sources:** Dataverse tables configured above
- **Fallback:** "I don't have that information. Please check the Pantry Supply Manager app or contact the office manager."

### Generative Actions (Plugin Actions)
- **Enabled:** Yes
- Allows the agent to automatically call Power Automate flows when needed
- Configured via the connector actions in Copilot Studio
