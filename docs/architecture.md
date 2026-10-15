# Solution architecture (SharePoint edition)

One Power Platform solution, `PantrySupplyOrdering` (publisher prefix `cr`), imported from `PantrySupplyOrdering_SharePoint.zip`. Inventory, orders and suppliers live in **SharePoint lists** on one site. The site address is the solution's environment variable **Pantry SharePoint site** (`cr_PantrySiteUrl`).

```
 Staff / approver / pantry admin
            │
            ▼
 ┌──────────────────────────┐        ┌───────────────────────────┐
 │ Canvas app               │        │ Copilot Studio agent      │
 │ Pantry Supply Ordering   │        │ Pantry Supply Assistant   │
 │ Dashboard · New request  │        │ SharePoint "Get items":   │
 │ My requests · Inventory  │        │ stock · orders · lines ·  │
 │ Approvals · Receiving    │        │ suppliers (read-only)     │
 └────────────┬─────────────┘        └─────────────┬─────────────┘
              │ SharePoint connector                │
              ▼                                     ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ SharePoint site "Office Pantry": Pantry Items · Pantry Suppliers │
 │  · Pantry Orders · Pantry Order Lines · Pantry Approval History  │
 └───────┬──────────────────────────┬──────────────────────┬────────┘
         │ Order Status = Submitted │ Order Status =       │ every day 08:00 IST
         ▼ (checked every minute)   ▼ Approved             ▼
 ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────────┐
 │ Flow: Pantry Order   │  │ Flow: Pantry Supplier│  │ Flow: Pantry Daily    │
 │ Approval             │  │ Order Email          │  │ Low Stock Alert       │
 │ over ₹5,000 or 50 u. │  │ PO email per supplier│  │ email table of items  │
 │ → Approvals request  │  │ → mark Ordered       │  │ at/below minimum      │
 │ else → auto-approve  │  └──────────┬───────────┘  └──────────┬────────────┘
 └──────────┬───────────┘             │                         │
            ▼                         ▼                         ▼
   Office manager (Outlook/Teams)   Suppliers (Outlook)    Pantry admin (Outlook)
   Requester (Outlook)

 Flow: Pantry - Create SharePoint site and lists (run once) → site, lists, columns, sample data
```

## Lists
Every list's **Title** column holds its name field.

| List | Title is | Other columns (internal name) |
|---|---|---|
| Pantry Suppliers | Supplier name | Contact Person, Email, Phone, Address, Website, Category (`SupplierCategory`, choice), Notes |
| Pantry Items | Item name | SKU, Category (choice), Unit of Measure (`Unit`, choice), Current Stock, Minimum Stock Level (`MinimumStock`), Reorder Quantity, Unit Price, Preferred Supplier (lookup → Pantry Suppliers), Storage Location, Description |
| Pantry Orders | Order number | Order Status (choice), Approval Status (choice), Order Date, Required By Date, Approval Date, Total Amount, Requested By (email), Requester Name, Approved By, Justification, Approver Comments, Delivery Address |
| Pantry Order Lines | Item name | Supply Order (lookup → Pantry Orders), Pantry Item (lookup → Pantry Items), Supplier (lookup → Pantry Suppliers), Quantity, Unit Price, Total Cost |
| Pantry Approval History | Record title | Supply Order (lookup), Action (`ApprovalAction`, choice), Approver, Action Date, Comments, Previous Status, New Status |

## Order lifecycle
| Order Status | Set by | What happens |
|---|---|---|
| Draft | App | Order and its lines are written |
| Submitted | App | The approval flow picks it up within about a minute |
| Approved | Approval flow (automatic or manager) or the app's Approvals screen | The supplier flow emails suppliers. The requester is emailed |
| Rejected | Approval flow or the app's Approvals screen | The requester is emailed with the reason |
| Ordered | Supplier flow | Order Date set |
| Received | App's Receiving screen | Line quantities are added to Current Stock |
| Cancelled | App's My requests (Draft or Submitted only) | Nothing is sent |

## Business rules
- **Inventory check:** staff can only request items whose Current Stock ≤ Minimum Stock Level.
  - The UI disables well-stocked items.
  - The submit step re-reads live stock from the list.
  - Pantry admins can override.
- **Approval limits:** Total Amount > ₹5,000 **or** total units > 50 → office manager approval. Otherwise the order is approved automatically. The approval flow enforces this, and the app previews it.

## How the flows talk to SharePoint
- **Triggers:** "When an item is created or modified" on Pantry Orders, with trigger conditions. The approval flow only starts when Order Status = Submitted and Approval Status is empty. It sets Approval Status to Pending first, so it never re-triggers itself.
- **Reads and writes:** "Send an HTTP request to SharePoint" (REST), addressing columns by internal name and lookups by `…Id`.
  - Filtering lines by order is done on the server (`SupplyOrderId eq {ID}`).
  - Text people type goes through a Compose step first, so it's always valid JSON.

## Source layout
| Path | What |
|---|---|
| `solution/sharepoint.py` | List and column definitions, site URL, sample data loader |
| `solution/flows.py` | The four flows, including approval limits and recipients |
| `solution/generate_solution.py` | Builds `PantrySupplyOrdering_SharePoint.zip` |
| `power-apps/canvas-app/generate_screens.py` | Generates the app's `Src/*.pa.yaml` (design system plus screens) |
| `power-apps/canvas-app/validate_app.py` | Property, enum and layout checks before packing |
| `copilot-agent/workspace/` | Copilot Studio agent source (instructions and SharePoint tools) |
| `sample-data/` | Supplier and pantry item data the setup flow loads |
