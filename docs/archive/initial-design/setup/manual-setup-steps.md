# Manual Setup Steps - Pantry Supply Ordering System

Complete these steps in https://make.powerapps.com in your dev environment.

---

## Step 1: Create a Solution

1. Go to **Solutions** > **+ New solution**
2. Display name: `Pantry Supply Ordering`
3. Publisher: Create new with prefix `cr`, option value prefix `10000`
4. Click **Create**
5. Open the solution — all tables below are created INSIDE this solution

---

## Step 2: Create Global Choice Columns (Option Sets)

Inside the solution, click **+ New** > **More** > **Choice**

### Choice 1: Item Category
| Value | Label |
|-------|-------|
| 100000000 | Coffee |
| 100000001 | Snacks |
| 100000002 | Beverages |
| 100000003 | Condiments |
| 100000004 | Cleaning Supplies |
| 100000005 | Other |

### Choice 2: Item Unit
| Value | Label |
|-------|-------|
| 100000000 | Pods |
| 100000001 | Packets |
| 100000002 | Boxes |
| 100000003 | Bottles |
| 100000004 | Units |

### Choice 3: Order Status
| Value | Label |
|-------|-------|
| 100000000 | Draft |
| 100000001 | Submitted |
| 100000002 | Pending Approval |
| 100000003 | Approved |
| 100000004 | Rejected |
| 100000005 | Sent to Supplier |
| 100000006 | Delivered |
| 100000007 | Cancelled |

### Choice 4: Approval Status
| Value | Label |
|-------|-------|
| 100000000 | Pending |
| 100000001 | Approved |
| 100000002 | Rejected |

### Choice 5: Approval Action
| Value | Label |
|-------|-------|
| 100000000 | Submitted |
| 100000001 | Approved |
| 100000002 | Rejected |
| 100000003 | Escalated |

### Choice 6: Supplier Category
| Value | Label |
|-------|-------|
| 100000000 | Coffee |
| 100000001 | Snacks |
| 100000002 | Beverages |
| 100000003 | General |

---

## Step 3: Create Tables

Create tables IN THIS ORDER (dependencies matter):

### Table 1: Supplier
- **+ New** > **Table**
- Display name: `Supplier`, Plural: `Suppliers`
- Ownership: **Organization**
- Primary column name: `Supplier Name` (max 200 chars)
- Click **Save**

**Add columns** (click the table > **+ New column**):

| Display Name | Data Type | Required | Notes |
|---|---|---|---|
| Contact Person | Text (100) | Required | |
| Email | Text (200) | Required | Format: Email |
| Phone | Text (50) | Optional | Format: Phone |
| Address | Multiline Text (2000) | Optional | |
| Category | Choice (multi-select) | Required | Use "Supplier Category" global choice |
| Lead Time (Days) | Whole Number | Optional | Min: 0, Max: 365 |
| Is Active | Yes/No | Required | Default: Yes |
| Contract End Date | Date Only | Optional | |
| Notes | Multiline Text (4000) | Optional | |

---

### Table 2: Pantry Item
- Display name: `Pantry Item`, Plural: `Pantry Items`
- Ownership: **Organization**
- Primary column: `Item Name` (max 100 chars)

**Add columns:**

| Display Name | Data Type | Required | Notes |
|---|---|---|---|
| Category | Choice | Required | Use "Item Category" global choice |
| Current Stock | Whole Number | Required | Min: 0, Max: 999999 |
| Max Stock Level | Whole Number | Required | Min: 1, Max: 999999 |
| Reorder Point | Whole Number | Required | Min: 0, Max: 999999 |
| Unit | Choice | Required | Use "Item Unit" global choice |
| Unit Price | Currency | Required | Precision: 2 |
| Preferred Supplier | Lookup | Optional | Related table: Supplier |
| Last Ordered Date | Date Only | Optional | |
| Last Restocked Date | Date Only | Optional | |
| Is Active | Yes/No | Required | Default: Yes |

---

### Table 3: Supply Order
- Display name: `Supply Order`, Plural: `Supply Orders`
- Ownership: **User or team** (enables row-level security)
- Primary column: `Order Number` (max 20 chars)
  - After creating, set **Autonumber** format: `ORD-{SEQNUM:5}`

**Add columns:**

| Display Name | Data Type | Required | Notes |
|---|---|---|---|
| Order Date | Date and Time | Required | |
| Order Status | Choice | Required | Use "Order Status" global choice, Default: Draft |
| Total Amount | Currency | Required | Precision: 2 |
| Total Quantity | Whole Number | Required | |
| Requires Approval | Yes/No | Required | Default: No |
| Approval Status | Choice | Optional | Use "Approval Status" global choice |
| Approval Date | Date and Time | Optional | |
| Approval Comments | Multiline Text (4000) | Optional | |
| Supplier | Lookup | Optional | Related table: Supplier |
| Supplier Email Sent | Yes/No | Required | Default: No |
| Expected Delivery | Date Only | Optional | |
| Delivery Date | Date Only | Optional | |
| Notes | Multiline Text (4000) | Optional | |

---

### Table 4: Order Line Item
- Display name: `Order Line Item`, Plural: `Order Line Items`
- Ownership: **Organization**
- Primary column: `Line Item` (max 100 chars)

**Add columns:**

| Display Name | Data Type | Required | Notes |
|---|---|---|---|
| Order | Lookup | Required | Related table: Supply Order, **Cascade delete: Cascade** |
| Pantry Item | Lookup | Required | Related table: Pantry Item |
| Quantity | Whole Number | Required | Min: 1 |
| Unit Price | Currency | Required | Precision: 2 |
| Line Total | Currency | Optional | Precision: 2 |
| Current Stock at Order | Whole Number | Optional | |

---

### Table 5: Approval History
- Display name: `Approval History`, Plural: `Approval History`
- Ownership: **Organization**
- Primary column: `Record` (max 100 chars)
  - After creating, set **Autonumber** format: `APR-{SEQNUM:5}`

**Add columns:**

| Display Name | Data Type | Required | Notes |
|---|---|---|---|
| Order | Lookup | Required | Related table: Supply Order, **Cascade delete: Cascade** |
| Action | Choice | Required | Use "Approval Action" global choice |
| Action Date | Date and Time | Required | |
| Comments | Multiline Text (4000) | Optional | |

---

## Step 4: Create Environment Variables

In the solution, **+ New** > **More** > **Environment variable**

| Display Name | Type | Default Value |
|---|---|---|
| Budget Approval Threshold | Decimal Number | 200 |
| Quantity Approval Threshold | Decimal Number | 50 |
| Approver Email | Text | *(your manager's email)* |
| Low Stock Alert Recipients | Text | *(semicolon-separated emails)* |

---

## Step 5: Load Sample Data

Go to each table and click **+ New row** or use **Import data from Excel**.
Use the CSV files in `solution/SampleData/`:
1. Import **Suppliers** first (3 records)
2. Import **Pantry Items** second (15 records), then set Preferred Supplier lookups

---

## Step 6: Create Cloud Flows

See the detailed flow definitions in the `power-automate/` folder:
- `approval-flow.md` — Approval workflow
- `supplier-order-flow.md` — Supplier email automation
- `low-stock-alert-flow.md` — Daily low stock notification

---

## Step 7: Build the Canvas App

See `power-apps/app-design.md` and `power-apps/formulas.md` for complete screen layouts and Power Fx code.

---

## Step 8: Set Up Copilot Agent

See `copilot-agent/agent-config.md` and `copilot-agent/topics.md`.

---

## Estimated Time: 45-60 minutes for tables + data, then flows and app on top.
