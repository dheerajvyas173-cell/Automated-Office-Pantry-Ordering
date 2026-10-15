# Sample data

You don't need to import these files. The **Pantry - Create SharePoint site and lists** flow loads them into the lists when it creates them. They're kept here as the source for that flow, and so you can see what the demo data contains.

| File | List | Rows |
|------|------|------|
| `1_Suppliers.csv` | Pantry Suppliers | 5 |
| `2_PantryItems.csv` | Pantry Items | 24 |

Each pantry item's **Preferred Supplier** is linked to the supplier with the same name.

Supplier emails use the reserved `example.com` domain, so no real company receives test orders. To test the supplier email end to end, change one supplier's **Email** in the Pantry Suppliers list to your own address.

## Test scenarios covered
Prices are in INR.

| Scenario | Items |
|----------|-------|
| Out of stock (stock 0) | Masala Chai Premix 1kg, Roasted Makhana 100g |
| Low stock (at or below minimum) | Coffee Beans Arabica 1kg, Green Tea Bags, Sparkling Water 500ml, Milk Toned 1L, Greek Yogurt Cups, Apples (Shimla), Granola Bars, Hand Wash Refill 1L, Paper Cups 200ml, Sugar Sachets |
| Well stocked (staff can't request them; pantry admins can) | Mineral Water 1L, Digestive Biscuits 250g, Mixed Nuts 500g, Tissue Box and others |
| Every item category and supplier | All 9 categories and all 5 suppliers have at least one item |

The **Pantry Daily Low Stock Alert** flow should report the 12 out-of-stock and low-stock items.
