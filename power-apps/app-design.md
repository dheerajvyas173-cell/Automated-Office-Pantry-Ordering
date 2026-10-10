# Power Apps Canvas App Design

## App Name: Pantry Supply Manager

### App Properties
- **Format**: Tablet (can also work on phone)
- **Theme**: Custom (Office Blue/Green palette)
- **Data Sources**: Dataverse (PantryItems, SupplyOrders, OrderLineItems, Suppliers)

---

## Screen 1: Home Screen (ScrHome)

### Layout
```
┌─────────────────────────────────────────────────────┐
│  🏢 Office Pantry Supply Manager          [User] ▼  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐      │
│  │   📦      │  │   📋      │  │   📊      │      │
│  │  New      │  │  My       │  │  Inventory │      │
│  │  Order    │  │  Orders   │  │  Dashboard │      │
│  └───────────┘  └───────────┘  └───────────┘      │
│                                                     │
│  ┌───────────────────────────────────────────┐      │
│  │  ⚠️ Low Stock Alerts                      │      │
│  │  ┌─────────────────────────────────────┐  │      │
│  │  │ Honey Sachets - 2/10 remaining      │  │      │
│  │  │ Green Tea Bags - 3/10 remaining     │  │      │
│  │  │ Dried Fruit Mix - 4/15 remaining    │  │      │
│  │  └─────────────────────────────────────┘  │      │
│  └───────────────────────────────────────────┘      │
│                                                     │
│  ┌───────────────────────────────────────────┐      │
│  │  📈 Recent Orders                         │      │
│  │  ORD-00012  Oct 8   Approved    $145.00   │      │
│  │  ORD-00011  Oct 5   Delivered   $89.50    │      │
│  │  ORD-00010  Oct 1   Delivered   $210.00   │      │
│  └───────────────────────────────────────────┘      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Key Controls
- **galLowStock**: Gallery showing PantryItems where `CurrentStock <= ReorderPoint`
- **galRecentOrders**: Gallery showing top 5 recent SupplyOrders
- **btnNewOrder**: Navigate to Order Form screen
- **btnMyOrders**: Navigate to Order History screen
- **btnDashboard**: Navigate to Inventory Dashboard screen

---

## Screen 2: New Order Screen (ScrNewOrder)

### Layout
```
┌─────────────────────────────────────────────────────┐
│  ← Back    New Supply Order                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Category Filter: [All ▼] [Coffee] [Snacks] [Bev]  │
│                                                     │
│  ┌─ Available Items ─────────────────────────────┐  │
│  │ ┌──────┐ Nespresso Ristretto Pods    $0.75   │  │
│  │ │ IMG  │ In Stock: 120  Unit: Pods           │  │
│  │ │      │ Qty: [___] [+ Add to Order]          │  │
│  │ └──────┘                                      │  │
│  │ ┌──────┐ Nespresso Lungo Pods        $0.75   │  │
│  │ │ IMG  │ In Stock: 45   Unit: Pods    ⚠️     │  │
│  │ │      │ Qty: [___] [+ Add to Order]          │  │
│  │ └──────┘                                      │  │
│  │ ┌──────┐ Green Tea Bags (100 pack)   $8.50   │  │
│  │ │ IMG  │ In Stock: 3    Unit: Boxes   🔴     │  │
│  │ │      │ Qty: [___] [+ Add to Order]          │  │
│  │ └──────┘                                      │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌─ Order Summary ───────────────────────────────┐  │
│  │ Items: 3           Total Qty: 25              │  │
│  │ Subtotal: $45.00                              │  │
│  │ ⓘ This order will be auto-approved            │  │
│  │                                               │  │
│  │ Notes: [________________________]              │  │
│  │                                               │  │
│  │        [Cancel]        [Submit Order]          │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Key Controls
- **galItems**: Gallery of active PantryItems with stock indicators
- **drpCategory**: Dropdown to filter items by category
- **txtQty**: Text input for quantity per item
- **btnAddItem**: Adds item to order collection (colOrderItems)
- **galOrderSummary**: Gallery of items added to current order
- **lblApprovalNote**: Dynamic label showing whether approval is required
- **btnSubmit**: Submit order to Dataverse
- **btnCancel**: Clear order and navigate back

### Stock Level Indicators
- 🟢 Green: Stock > 50% of MaxStock
- 🟡 Yellow (⚠️): Stock between ReorderPoint and 50% of MaxStock
- 🔴 Red: Stock ≤ ReorderPoint

---

## Screen 3: Order History Screen (ScrOrderHistory)

### Layout
```
┌─────────────────────────────────────────────────────┐
│  ← Back    My Orders                    [Filter ▼]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Status: [All ▼]  Date Range: [This Month ▼]       │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ ORD-00012    Oct 8, 2026                      │  │
│  │ Status: ✅ Approved    Total: $145.00          │  │
│  │ Items: Coffee Pods ×50, Sugar ×5               │  │
│  │ Approved by: Jane Manager                      │  │
│  ├───────────────────────────────────────────────┤  │
│  │ ORD-00011    Oct 5, 2026                      │  │
│  │ Status: 📦 Delivered   Total: $89.50           │  │
│  │ Items: Granola Bars ×10, Mixed Nuts ×5         │  │
│  ├───────────────────────────────────────────────┤  │
│  │ ORD-00010    Oct 1, 2026                      │  │
│  │ Status: ❌ Rejected    Total: $520.00          │  │
│  │ Items: Sparkling Water ×200                    │  │
│  │ Reason: "Exceeds monthly budget - resubmit    │  │
│  │          with reduced quantity"                 │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Screen 4: Inventory Dashboard (ScrDashboard)

### Layout
```
┌─────────────────────────────────────────────────────┐
│  ← Back    Inventory Dashboard                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Total    │ │ Low      │ │ Out of   │           │
│  │ Items    │ │ Stock    │ │ Stock    │           │
│  │   15     │ │    3     │ │    0     │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│                                                     │
│  ┌─ Stock Levels by Category ────────────────────┐  │
│  │                                               │  │
│  │  Coffee     ████████████████░░░░  80%          │  │
│  │  Snacks     ██████████░░░░░░░░░░  50%          │  │
│  │  Beverages  ████░░░░░░░░░░░░░░░░  25%   ⚠️    │  │
│  │  Condiments ██████████████░░░░░░  65%          │  │
│  │                                               │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌─ Items Below Reorder Point ───────────────────┐  │
│  │  Item              Stock   Reorder  Action     │  │
│  │  Honey Sachets      2/10     3     [Order]     │  │
│  │  Green Tea Bags     3/10     3     [Order]     │  │
│  │  Dried Fruit Mix    4/15     5     [Order]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌─ Monthly Spending ───────────────────────────┐   │
│  │  Jul: $450  Aug: $380  Sep: $520  Oct: $145   │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Key Controls
- **lblTotalItems**: `CountRows(PantryItems)`
- **lblLowStock**: `CountRows(Filter(PantryItems, CurrentStock <= ReorderPoint And CurrentStock > 0))`
- **lblOutOfStock**: `CountRows(Filter(PantryItems, CurrentStock = 0))`
- **galLowItems**: Gallery of items below reorder point with quick-order button

---

## Navigation Flow

```
Home Screen
    ├── New Order → Submit → Confirmation → Home
    ├── My Orders → Order Detail → Home
    └── Inventory Dashboard → Quick Order → New Order
```

## App-Level Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `varCurrentUser` | Record | Currently logged-in user info |
| `varBudgetThreshold` | Number | Approval threshold ($200 default) |
| `varQuantityThreshold` | Number | Quantity threshold (50 default) |
| `colOrderItems` | Collection | Items in the current order being built |
