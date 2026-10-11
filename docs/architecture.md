# Solution architecture

One Power Platform solution (`PantrySupplyOrdering`, publisher prefix `cr`). Import `Step6_Copilot_Agent.zip`, which contains every component below.

```
 Staff / approver / pantry admin
            │
            ▼
 ┌──────────────────────────┐        ┌───────────────────────────┐
 │ Canvas app               │        │ Copilot Studio agent      │
 │ Pantry Supply Ordering   │        │ Pantry Supply Assistant   │
 │ Dashboard · New request  │        │ stock · orders · lines ·  │
 │ My requests · Inventory  │        │ suppliers (read-only)     │
 │ Approvals · Receiving    │        └─────────────┬─────────────┘
 └────────────┬─────────────┘                      │
              │ Patch / Filter (delegated)          │ Dataverse List rows
              ▼                                     ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ Dataverse: Pantry Items · Suppliers · Supply Orders ·            │
 │            Order Line Items · Approval History                   │
 └───────┬──────────────────────────┬──────────────────────┬────────┘
         │ Order Status = Submitted │ Order Status =       │ every day 08:00 IST
         ▼                          ▼ Approved             ▼
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
```

## Order lifecycle
| Status | Set by | What happens |
|---|---|---|
| Draft | App | Order header created, line items written |
| Submitted | App | Triggers the approval flow |
| Approved | Approval flow (auto or manager) or the app's Approvals screen | Triggers the supplier flow. The requester is emailed |
| Rejected | Approval flow or the app's Approvals screen | The requester is emailed with the reason |
| Ordered | Supplier flow | Suppliers emailed, Order Date set |
| Received | App's Receiving screen | Line quantities added to Current Stock |
| Cancelled | App's My requests (Draft or Submitted only) | Nothing is sent |

## Tables
| Table | Key columns |
|---|---|
| Pantry Items | Item Name, SKU, Category, Unit of Measure, Current Stock, Minimum Stock Level, Reorder Quantity, Unit Price, Preferred Supplier (lookup), Storage Location |
| Suppliers | Supplier Name, Contact Person, Email, Phone, Address, Website, Category |
| Supply Orders | Order Number, Order Status, Approval Status, Order Date, Required By Date, Approval Date, Total Amount, Requested By, Approved By, Justification, Approver Comments, Delivery Address |
| Order Line Items | Line Item Name, Supply Order, Pantry Item, Supplier (lookups), Quantity, Unit Price, Total Cost |
| Approval History | Approval Record, Supply Order (lookup), Action, Approver, Action Date, Comments, Previous Status, New Status |

The choices (Item Category, Unit, Order Status, Approval Status, Approval Action, Supplier Category) are global option sets.

## Business rules
- **Inventory check:** staff can request only items whose Current Stock ≤ Minimum Stock Level.
  - The UI disables well-stocked items.
  - The submit step re-reads live stock.
  - Pantry admins can override.
- **Approval limits:** Total Amount > ₹5,000 **or** total units > 50 → office manager approval. Otherwise the order is approved automatically. The approval flow enforces this, and the app previews it.

## Source layout
| Path | What |
|---|---|
| `solution/generate_solution.py` | Builds every solution ZIP (tables, choices, roles, flows, app, agent) |
| `solution/flows.py` | Flow definitions, including the approval limits and recipients |
| `power-apps/canvas-app/generate_screens.py` | Generates the app's `Src/*.pa.yaml` (design system plus screens) |
| `power-apps/canvas-app/validate_app.py` | Property, enum and layout checks before packing |
| `power-apps/canvas-app/shell/` | App shell (properties, theme). The tables are added in Studio after import |
| `copilot-agent/workspace/` | Copilot Studio agent source (instructions and topics) |
| `dataverse/sample-data/` | Supplier and pantry item CSVs for import |
