# Sample Data for Testing

## Suppliers

| Supplier Name | Contact Person | Email | Category | Lead Time |
|--------------|----------------|-------|----------|-----------|
| CoffeeWorld Supplies | Sarah Johnson | orders@coffeeworld.com | Coffee, Beverages | 3 days |
| SnackMaster Inc. | Mike Chen | purchasing@snackmaster.com | Snacks, Condiments | 2 days |
| Office Essentials Co. | Lisa Park | orders@officeessentials.com | Coffee, Snacks, Beverages, General | 5 days |

## Pantry Items

| Item Name | Category | Current Stock | Max Stock | Reorder Point | Unit | Unit Price | Preferred Supplier |
|-----------|----------|--------------|-----------|---------------|------|-----------|-------------------|
| Nespresso Original Pods (Ristretto) | Coffee | 120 | 500 | 100 | Pods | $0.75 | CoffeeWorld Supplies |
| Nespresso Original Pods (Lungo) | Coffee | 45 | 500 | 100 | Pods | $0.75 | CoffeeWorld Supplies |
| Ground Coffee (Colombian) 1kg | Coffee | 8 | 20 | 5 | Packets | $12.50 | CoffeeWorld Supplies |
| Instant Coffee (Nescafe) 200g | Coffee | 15 | 30 | 8 | Packets | $6.99 | CoffeeWorld Supplies |
| Green Tea Bags (100 pack) | Beverages | 3 | 10 | 3 | Boxes | $8.50 | CoffeeWorld Supplies |
| Black Tea Bags (100 pack) | Beverages | 5 | 10 | 3 | Boxes | $7.00 | CoffeeWorld Supplies |
| Sparkling Water (500ml) | Beverages | 48 | 100 | 25 | Bottles | $1.20 | Office Essentials Co. |
| Mixed Nuts (500g) | Snacks | 12 | 30 | 8 | Packets | $9.99 | SnackMaster Inc. |
| Granola Bars (Box of 12) | Snacks | 6 | 20 | 5 | Boxes | $5.49 | SnackMaster Inc. |
| Dark Chocolate (100g) | Snacks | 20 | 50 | 10 | Units | $3.25 | SnackMaster Inc. |
| Dried Fruit Mix (400g) | Snacks | 4 | 15 | 5 | Packets | $7.99 | SnackMaster Inc. |
| Sugar (1kg) | Condiments | 10 | 20 | 5 | Packets | $2.50 | Office Essentials Co. |
| Milk (UHT 1L) | Condiments | 18 | 40 | 10 | Units | $1.80 | Office Essentials Co. |
| Oat Milk (1L) | Condiments | 7 | 20 | 5 | Units | $3.50 | Office Essentials Co. |
| Honey Sachets (50 pack) | Condiments | 2 | 10 | 3 | Boxes | $12.00 | SnackMaster Inc. |

## Sample Orders for Testing

### Order 1: Small order (auto-approved)
- **Requested By**: John Smith
- **Items**: Nespresso Ristretto Pods × 20, Sugar × 2
- **Total**: $20.00
- **Status**: Should auto-approve (under $200 and under 50 units)

### Order 2: Large order (requires approval)
- **Requested By**: Jane Doe
- **Items**: Nespresso Lungo Pods × 200, Ground Coffee × 10, Green Tea × 5
- **Total**: $292.50
- **Status**: Should require approval (over $200)

### Order 3: High quantity order (requires approval)
- **Requested By**: Bob Wilson
- **Items**: Sparkling Water × 60
- **Total**: $72.00
- **Status**: Should require approval (over 50 units)

## Low Stock Alert Test Scenarios

The following items should trigger low stock alerts based on sample data:

| Item | Current Stock | Reorder Point | Status |
|------|--------------|---------------|--------|
| Green Tea Bags | 3 | 3 | LOW STOCK (at reorder point) |
| Honey Sachets | 2 | 3 | LOW STOCK (below reorder point) |
| Dried Fruit Mix | 4 | 5 | LOW STOCK (below reorder point) |

## Copilot Agent Test Queries

Use these queries to test the Copilot Agent:

1. "How many coffee pods are left?"
   - Expected: "Ristretto: 120 pods, Lungo: 45 pods"

2. "When was the last order placed?"
   - Expected: Returns most recent order date and details

3. "Which items are running low?"
   - Expected: Lists Green Tea, Honey Sachets, Dried Fruit Mix

4. "What's the contact info for our coffee supplier?"
   - Expected: CoffeeWorld Supplies, Sarah Johnson, orders@coffeeworld.com

5. "How much did we spend on snacks last month?"
   - Expected: Sum of approved snack orders from previous month
