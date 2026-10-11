# Dataverse Table Schemas

## Table: PantryItems

Stores the inventory catalog of all pantry supplies.

**Table Properties:**
- Display Name: `Pantry Item`
- Plural Name: `Pantry Items`
- Schema Name: `cr_pantryitem`
- Ownership: Organization
- Enable Auditing: Yes

| Column Name | Schema Name | Type | Required | Description |
|-------------|-------------|------|----------|-------------|
| Item Name | `cr_name` | Text (100) | Yes | Name of the supply item |
| Item ID | `cr_pantryitemid` | Auto-number (PNT-{SEQNUM:4}) | Yes | Unique identifier |
| Category | `cr_category` | Choice | Yes | Coffee / Snacks / Beverages / Condiments / Cleaning / Other |
| Current Stock | `cr_currentstock` | Whole Number | Yes | Current quantity in stock |
| Max Stock Level | `cr_maxstocklevel` | Whole Number | Yes | Maximum storage capacity |
| Reorder Point | `cr_reorderpoint` | Whole Number | Yes | Stock level that triggers reorder alert |
| Unit | `cr_unit` | Choice | Yes | Pods / Packets / Boxes / Bottles / Units |
| Unit Price | `cr_unitprice` | Currency | Yes | Price per unit from supplier |
| Preferred Supplier | `cr_preferredsupplier` | Lookup (Suppliers) | No | Default supplier for this item |
| Last Ordered Date | `cr_lastordereddate` | Date Only | No | When this item was last ordered |
| Last Restocked Date | `cr_lastrestockeddate` | Date Only | No | When stock was last received |
| Item Image | `cr_itemimage` | Image | No | Photo of the item |
| Is Active | `cr_isactive` | Yes/No | Yes | Whether item is currently stocked |
| Stock Status | `cr_stockstatus` | Calculated | Auto | "In Stock" / "Low Stock" / "Out of Stock" |

**Calculated Column Formula for Stock Status:**
```
If(cr_currentstock = 0, "Out of Stock",
   If(cr_currentstock <= cr_reorderpoint, "Low Stock",
      "In Stock"))
```

**Business Rule:**
- When `CurrentStock` falls below `ReorderPoint`, set `StockStatus` to "Low Stock"

---

## Table: SupplyOrders

Stores all supply order requests.

**Table Properties:**
- Display Name: `Supply Order`
- Plural Name: `Supply Orders`
- Schema Name: `cr_supplyorder`
- Ownership: User
- Enable Auditing: Yes

| Column Name | Schema Name | Type | Required | Description |
|-------------|-------------|------|----------|-------------|
| Order Number | `cr_ordernumber` | Auto-number (ORD-{SEQNUM:5}) | Yes | Unique order identifier |
| Order Date | `cr_orderdate` | Date and Time | Yes | When the order was placed |
| Requested By | `cr_requestedby` | Lookup (Users) | Yes | Employee who placed the order |
| Order Status | `cr_orderstatus` | Choice | Yes | Draft / Submitted / Pending Approval / Approved / Rejected / Sent to Supplier / Delivered / Cancelled |
| Total Amount | `cr_totalamount` | Currency | Yes | Total order value (rollup from line items) |
| Total Quantity | `cr_totalquantity` | Whole Number | Yes | Total items ordered (rollup) |
| Requires Approval | `cr_requiresapproval` | Yes/No | Yes | Whether this order needs manager approval |
| Approval Status | `cr_approvalstatus` | Choice | No | Pending / Approved / Rejected |
| Approved By | `cr_approvedby` | Lookup (Users) | No | Manager who approved/rejected |
| Approval Date | `cr_approvaldate` | Date and Time | No | When approval decision was made |
| Approval Comments | `cr_approvalcomments` | Multiline Text | No | Manager's comments on approval/rejection |
| Supplier | `cr_supplier` | Lookup (Suppliers) | No | Supplier the order is sent to |
| Supplier Email Sent | `cr_supplieremailsent` | Yes/No | Yes | Whether supplier has been notified |
| Expected Delivery | `cr_expecteddelivery` | Date Only | No | Expected delivery date |
| Delivery Date | `cr_deliverydate` | Date Only | No | Actual delivery date |
| Notes | `cr_notes` | Multiline Text | No | Additional notes |

**Business Rules:**
1. If `TotalAmount > 200` OR `TotalQuantity > 50`, set `RequiresApproval` = Yes
2. When `OrderStatus` = "Delivered", update `PantryItems.CurrentStock` for each line item

---

## Table: OrderLineItems

Stores individual items within an order.

**Table Properties:**
- Display Name: `Order Line Item`
- Plural Name: `Order Line Items`
- Schema Name: `cr_orderlineitem`
- Ownership: Organization
- Enable Auditing: Yes

| Column Name | Schema Name | Type | Required | Description |
|-------------|-------------|------|----------|-------------|
| Line Item ID | `cr_orderlineitemid` | GUID | Yes | Primary key |
| Order | `cr_order` | Lookup (SupplyOrders) | Yes | Parent order |
| Pantry Item | `cr_pantryitem` | Lookup (PantryItems) | Yes | Item being ordered |
| Quantity | `cr_quantity` | Whole Number | Yes | Quantity requested |
| Unit Price | `cr_unitprice` | Currency | Yes | Price at time of order |
| Line Total | `cr_linetotal` | Currency | Calculated | Quantity × Unit Price |
| Current Stock at Order | `cr_currentstockatorder` | Whole Number | No | Snapshot of stock when ordered |

---

## Table: Suppliers

Stores supplier contact information.

**Table Properties:**
- Display Name: `Supplier`
- Plural Name: `Suppliers`
- Schema Name: `cr_supplier`
- Ownership: Organization
- Enable Auditing: Yes

| Column Name | Schema Name | Type | Required | Description |
|-------------|-------------|------|----------|-------------|
| Supplier Name | `cr_name` | Text (200) | Yes | Company name |
| Contact Person | `cr_contactperson` | Text (100) | Yes | Primary contact name |
| Email | `cr_email` | Text (200) | Yes | Order submission email |
| Phone | `cr_phone` | Phone | No | Contact phone number |
| Address | `cr_address` | Multiline Text | No | Business address |
| Category | `cr_category` | Choice (Multi) | Yes | Coffee / Snacks / Beverages / General |
| Lead Time Days | `cr_leadtimedays` | Whole Number | No | Typical delivery time in days |
| Is Active | `cr_isactive` | Yes/No | Yes | Whether currently doing business |
| Contract End Date | `cr_contractenddate` | Date Only | No | When current contract expires |
| Notes | `cr_notes` | Multiline Text | No | Additional notes |

---

## Table: ApprovalHistory

Audit trail for all approval decisions.

**Table Properties:**
- Display Name: `Approval History`
- Plural Name: `Approval History`
- Schema Name: `cr_approvalhistory`
- Ownership: Organization
- Enable Auditing: Yes

| Column Name | Schema Name | Type | Required | Description |
|-------------|-------------|------|----------|-------------|
| Record ID | `cr_approvalhistoryid` | GUID | Yes | Primary key |
| Order | `cr_order` | Lookup (SupplyOrders) | Yes | Related order |
| Action | `cr_action` | Choice | Yes | Submitted / Approved / Rejected / Escalated |
| Action By | `cr_actionby` | Lookup (Users) | Yes | Person who took the action |
| Action Date | `cr_actiondate` | Date and Time | Yes | When the action occurred |
| Comments | `cr_comments` | Multiline Text | No | Notes/reason for the action |

---

## Table Relationships

```
PantryItems (1) ──────── (N) OrderLineItems
Suppliers   (1) ──────── (N) PantryItems (Preferred Supplier)
Suppliers   (1) ──────── (N) SupplyOrders
SupplyOrders (1) ──────── (N) OrderLineItems
SupplyOrders (1) ──────── (N) ApprovalHistory
Users        (1) ──────── (N) SupplyOrders (Requested By)
Users        (1) ──────── (N) SupplyOrders (Approved By)
```

## Choice Column Values

### PantryItems.Category
| Value | Label |
|-------|-------|
| 1 | Coffee |
| 2 | Snacks |
| 3 | Beverages |
| 4 | Condiments |
| 5 | Cleaning Supplies |
| 6 | Other |

### PantryItems.Unit
| Value | Label |
|-------|-------|
| 1 | Pods |
| 2 | Packets |
| 3 | Boxes |
| 4 | Bottles |
| 5 | Units |

### SupplyOrders.OrderStatus
| Value | Label |
|-------|-------|
| 1 | Draft |
| 2 | Submitted |
| 3 | Pending Approval |
| 4 | Approved |
| 5 | Rejected |
| 6 | Sent to Supplier |
| 7 | Delivered |
| 8 | Cancelled |
