# Sample Data for Testing

Ready-to-import CSV files are in [`sample-data/`](sample-data/). Their column headers match the
table display names, and their category and unit values match the solution's choice lists, so the
Power Apps import wizard maps them automatically.

| File | Table | Rows |
|------|-------|------|
| `1_Suppliers.csv` | Supplier | 5 |
| `2_PantryItems.csv` | Pantry Item | 24 |

Import the suppliers first: each pantry item's **Preferred Supplier** is matched to a supplier by name.

## How to import

1. Go to <https://make.powerapps.com> and select the **dev-ind-38104aa9** environment.
2. **Tables** → open **Supplier** → **Import** → **Import data from Excel** → upload `1_Suppliers.csv`.
3. Check that every column shows as mapped (select **Map columns** if not), then select **Import**.
4. Repeat for **Pantry Item** with `2_PantryItems.csv`.

Supplier emails use the reserved `example.com` domain, so no real company receives test orders.
To test the supplier email flow end to end, change one supplier's email to your own.

## Test scenarios covered

Prices are in INR.

| Scenario | Items |
|----------|-------|
| Out of stock (stock 0) | Masala Chai Premix 1kg, Roasted Makhana 100g |
| Low stock (at or below minimum) | Coffee Beans Arabica 1kg, Green Tea Bags, Sparkling Water 500ml, Milk Toned 1L, Greek Yogurt Cups, Apples (Shimla), Granola Bars, Hand Wash Refill 1L, Paper Cups 200ml, Sugar Sachets |
| Well stocked (staff can't request them; pantry admins can) | Mineral Water 1L, Digestive Biscuits 250g, Mixed Nuts 500g, Tissue Box and others |
| Every item category and supplier | All 9 categories and all 5 suppliers have at least one item |

The **Pantry Daily Low Stock Alert** flow should report the 12 out-of-stock and low-stock items.
