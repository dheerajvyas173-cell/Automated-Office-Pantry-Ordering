# Power Fx Formulas Reference

## App OnStart

```
// Set user context and configuration thresholds
Set(varCurrentUser, User());
Set(varBudgetThreshold, 200);
Set(varQuantityThreshold, 50);
ClearCollect(colOrderItems, Blank());
Clear(colOrderItems);
```

---

## Screen: Home (ScrHome)

### Low Stock Gallery (galLowStock)
**Items:**
```
Sort(
    Filter(
        PantryItems,
        cr_isactive = true,
        cr_currentstock <= cr_reorderpoint
    ),
    cr_currentstock,
    SortOrder.Ascending
)
```

**Subtitle (Stock Level):**
```
ThisItem.cr_currentstock & " / " & ThisItem.cr_maxstocklevel & " " & 
Switch(
    ThisItem.cr_unit,
    1, "pods",
    2, "packets",
    3, "boxes",
    4, "bottles",
    5, "units"
) & " remaining"
```

### Recent Orders Gallery (galRecentOrders)
**Items:**
```
SortByColumns(
    Filter(
        SupplyOrders,
        cr_requestedby.'Primary Email' = varCurrentUser.Email
    ),
    "cr_orderdate",
    SortOrder.Descending
)
```

---

## Screen: New Order (ScrNewOrder)

### Item Gallery Filter by Category (galItems)
**Items:**
```
Sort(
    Filter(
        PantryItems,
        cr_isactive = true,
        drpCategory.Selected.Value = "All" Or
        cr_category = drpCategory.Selected.Value
    ),
    cr_name,
    SortOrder.Ascending
)
```

### Stock Level Icon (icoStockLevel)
**Icon:**
```
If(
    ThisItem.cr_currentstock <= ThisItem.cr_reorderpoint,
    Icon.Warning,
    If(
        ThisItem.cr_currentstock <= ThisItem.cr_maxstocklevel * 0.5,
        Icon.Information,
        Icon.CheckBadge
    )
)
```

**Color:**
```
If(
    ThisItem.cr_currentstock <= ThisItem.cr_reorderpoint,
    Color.Red,
    If(
        ThisItem.cr_currentstock <= ThisItem.cr_maxstocklevel * 0.5,
        Color.Orange,
        Color.Green
    )
)
```

### Add to Order Button (btnAddItem)
**OnSelect:**
```
If(
    Value(txtQty.Text) > 0,
    // Check if item already in order
    If(
        CountRows(Filter(colOrderItems, ItemID = ThisItem.cr_pantryitemid)) > 0,
        // Update quantity
        UpdateIf(
            colOrderItems,
            ItemID = ThisItem.cr_pantryitemid,
            {Quantity: Quantity + Value(txtQty.Text)}
        ),
        // Add new item
        Collect(
            colOrderItems,
            {
                ItemID: ThisItem.cr_pantryitemid,
                ItemName: ThisItem.cr_name,
                Category: ThisItem.cr_category,
                UnitPrice: ThisItem.cr_unitprice,
                Quantity: Value(txtQty.Text),
                Unit: ThisItem.cr_unit,
                LineTotal: ThisItem.cr_unitprice * Value(txtQty.Text),
                CurrentStock: ThisItem.cr_currentstock,
                PreferredSupplier: ThisItem.cr_preferredsupplier
            }
        )
    );
    Reset(txtQty);
    Notify("Added to order", NotificationType.Success)
)
```

### Order Summary Calculations
**Total Amount (lblTotalAmount):**
```
Text(Sum(colOrderItems, LineTotal), "$#,##0.00")
```

**Total Quantity (lblTotalQty):**
```
Sum(colOrderItems, Quantity)
```

### Approval Required Indicator (lblApprovalNote)
**Text:**
```
If(
    Sum(colOrderItems, LineTotal) > varBudgetThreshold Or
    Sum(colOrderItems, Quantity) > varQuantityThreshold,
    "⚠️ This order exceeds thresholds and will require manager approval.",
    "✅ This order will be auto-approved."
)
```

### Submit Order Button (btnSubmitOrder)
**OnSelect:**
```
// Validate order has items
If(
    CountRows(colOrderItems) = 0,
    Notify("Please add items to your order", NotificationType.Error);
    Return()
);

// Determine if approval is required
Set(
    varNeedsApproval,
    Sum(colOrderItems, LineTotal) > varBudgetThreshold Or
    Sum(colOrderItems, Quantity) > varQuantityThreshold
);

// Create the order record
Set(
    varNewOrder,
    Patch(
        SupplyOrders,
        Defaults(SupplyOrders),
        {
            cr_orderdate: Now(),
            cr_orderstatus: If(varNeedsApproval, 3, 4),
            cr_totalamount: Sum(colOrderItems, LineTotal),
            cr_totalquantity: Sum(colOrderItems, Quantity),
            cr_requiresapproval: varNeedsApproval,
            cr_approvalstatus: If(varNeedsApproval, 1, 2),
            cr_supplieremailsent: false,
            cr_notes: txtOrderNotes.Text
        }
    )
);

// Create line items
ForAll(
    colOrderItems,
    Patch(
        OrderLineItems,
        Defaults(OrderLineItems),
        {
            cr_order: LookUp(SupplyOrders, cr_supplyorderid = varNewOrder.cr_supplyorderid),
            cr_pantryitem: LookUp(PantryItems, cr_pantryitemid = ThisRecord.ItemID),
            cr_quantity: ThisRecord.Quantity,
            cr_unitprice: ThisRecord.UnitPrice,
            cr_currentstockatorder: ThisRecord.CurrentStock
        }
    )
);

// Clear cart and navigate
Clear(colOrderItems);
Notify(
    If(
        varNeedsApproval,
        "Order submitted for approval!",
        "Order approved and sent to supplier!"
    ),
    NotificationType.Success
);
Navigate(ScrHome);
```

### Quantity Validation (txtQty)
**OnChange:**
```
If(
    Value(Self.Text) > ThisItem.cr_maxstocklevel - ThisItem.cr_currentstock,
    Notify(
        "Requested quantity exceeds available storage capacity",
        NotificationType.Warning
    )
)
```

---

## Screen: Order History (ScrOrderHistory)

### Order Status Display (lblStatus)
**Text:**
```
Switch(
    ThisItem.cr_orderstatus,
    1, "📝 Draft",
    2, "📤 Submitted",
    3, "⏳ Pending Approval",
    4, "✅ Approved",
    5, "❌ Rejected",
    6, "📧 Sent to Supplier",
    7, "📦 Delivered",
    8, "🚫 Cancelled"
)
```

### Filter by Status (drpStatusFilter)
**Items:**
```
["All", "Pending Approval", "Approved", "Rejected", "Delivered"]
```

### Filtered Orders Gallery
**Items:**
```
SortByColumns(
    Filter(
        SupplyOrders,
        cr_requestedby.'Primary Email' = varCurrentUser.Email,
        drpStatusFilter.Selected.Value = "All" Or
        Switch(
            drpStatusFilter.Selected.Value,
            "Pending Approval", cr_orderstatus = 3,
            "Approved", cr_orderstatus = 4,
            "Rejected", cr_orderstatus = 5,
            "Delivered", cr_orderstatus = 7
        )
    ),
    "cr_orderdate",
    SortOrder.Descending
)
```

---

## Screen: Inventory Dashboard (ScrDashboard)

### KPI Cards

**Total Active Items:**
```
CountRows(Filter(PantryItems, cr_isactive = true))
```

**Low Stock Count:**
```
CountRows(
    Filter(
        PantryItems,
        cr_isactive = true,
        cr_currentstock <= cr_reorderpoint,
        cr_currentstock > 0
    )
)
```

**Out of Stock Count:**
```
CountRows(
    Filter(
        PantryItems,
        cr_isactive = true,
        cr_currentstock = 0
    )
)
```

### Stock Percentage by Category (for bar chart data)
```
ClearCollect(
    colCategoryStock,
    AddColumns(
        GroupBy(
            Filter(PantryItems, cr_isactive = true),
            "cr_category",
            "Items"
        ),
        "StockPercent",
        Round(
            Sum(Items, cr_currentstock) / Sum(Items, cr_maxstocklevel) * 100,
            0
        )
    )
);
```

### Monthly Spending Calculation
```
ClearCollect(
    colMonthlySpend,
    AddColumns(
        GroupBy(
            Filter(
                SupplyOrders,
                cr_orderstatus = 4 Or cr_orderstatus = 6 Or cr_orderstatus = 7,
                cr_orderdate >= DateAdd(Today(), -6, TimeUnit.Months)
            ),
            "OrderMonth",
            "Orders"
        ),
        "TotalSpend", Sum(Orders, cr_totalamount)
    )
);
```

---

## Reusable Components

### Stock Level Bar Component
**Width formula (proportional to stock level):**
```
(ThisItem.cr_currentstock / ThisItem.cr_maxstocklevel) * Parent.Width
```

**Fill color:**
```
If(
    ThisItem.cr_currentstock / ThisItem.cr_maxstocklevel <= 0.2,
    RGBA(220, 38, 38, 1),    // Red
    If(
        ThisItem.cr_currentstock / ThisItem.cr_maxstocklevel <= 0.5,
        RGBA(245, 158, 11, 1), // Amber
        RGBA(34, 197, 94, 1)   // Green
    )
)
```
