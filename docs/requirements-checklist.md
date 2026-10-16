# Requirements checklist

Each assignment requirement, where the solution meets it, and how to show it in the demo.
Approval limits used throughout: **over ₹5,000 or over 50 units** needs the office manager.

| # | Requirement | Status | Where it lives |
|---|---|---|---|
| 1a | Power Apps form to request coffee, snacks and supplies | ✅ | Canvas app → **New request** screen |
| 1b | Inventory stored in SharePoint | ✅ | **Pantry Items** list on the Office Pantry SharePoint site (plus 4 related lists) |
| 1b | Check inventory before allowing an order | ✅ | New request, Inventory and Dashboard screens, plus a live re-check at submit |
| 2 | Approval only above a quantity or budget threshold | ✅ | Flow **Pantry Order Approval** (enforces it) and the app's cart (previews it) |
| 3 | Approved orders email the supplier automatically | ✅ | Flow **Pantry Supplier Order Email** |
| 4 | Copilot agent: stock levels, reorder dates, supplier details, last order | ✅ | Copilot Studio agent **Pantry Supply Assistant** (reads the SharePoint lists) |
| 5 | Notifications for approvals, rejections and low stock | ✅ | Approval flow emails plus the daily **Pantry Daily Low Stock Alert** |
| 6 | Presentation | ✅ | [presentation-guide.md](presentation-guide.md), [architecture.md](architecture.md), [security-considerations.md](security-considerations.md) |

## Notes

### Note 1: SharePoint as the data store (requirement 1)
- Five lists on one site: Pantry Items (inventory), Pantry Suppliers, Pantry Orders, Pantry Order Lines and Pantry Approval History. They're linked by lookup columns: item → preferred supplier, line → order, item and supplier.
- One flow, **Pantry - Create SharePoint site and lists**, builds everything: the site, the lists, the columns and the sample data. Setup is repeatable and nothing is built by hand.
- The site address is a solution **environment variable**, so the same solution can point to a test or production site.

### Note 2: Inventory check (requirement 1)
- Staff can only add items **at or below their minimum stock level**. For well-stocked items the **Add** and **Request** buttons are disabled, with the tooltip "Well stocked: no reorder needed yet".
- The catalog opens on **Needs restock**. Switch to **All items** to see everything with its stock badge (Out of stock / Low stock / Well stocked).
- **At submit**, the app re-reads live stock from the Pantry Items list. Someone may have restocked since the app loaded, so it blocks any item that is now well stocked and names it.
- A **Pantry Admin** can override and add any item. The app shows a warning toast when they do.

### Note 3: Approval threshold (requirement 2)
- The **flow enforces** the rule, so it can't be bypassed from the app. It adds up the order's line quantities and compares the total amount and units with the limits in its **Settings** step.
  - **Over a limit:** the office manager gets an email with **Approve / Reject** buttons, and the requester is emailed the outcome.
  - **Under both limits:** the order is approved automatically ("Auto-approved (under limits)"), logged in Approval History, and the requester is emailed.
- The **app previews** the rule in the cart: a green "Auto-approved" or amber "Needs office manager approval" note updates as you add items.
- The Approvals screen only lists orders that need a decision, and shows why ("Over ₹5,000" / "Over 50 units").

### Note 4: Supplier email (requirement 3)
When an order becomes **Approved**, whether manually or automatically, the supplier flow:
- groups the lines by supplier;
- emails each supplier an HTML purchase-order table;
- emails the pantry admin about any line with no supplier;
- marks the order **Ordered** with today's order date.

### Note 5: Copilot agent (requirement 4)
Four read-only SharePoint "Get items" tools: pantry stock, recent orders, recent order lines and suppliers. The agent's instructions include the inventory and approval rules. Try:
- "How many coffee pods are left?" or "How much Nescafe is left?"
- "When was the last order placed?"
- "What needs reordering and how much should we order?"
- "When did we last order coffee beans?"
- "Who supplies milk and what's their email?"
- "Do I need approval for an order of ₹6,000?"

### Note 6: Notifications (requirement 5)
| Event | Who | How |
|---|---|---|
| Order needs approval | Office manager | Outlook email with Approve / Reject buttons |
| Approved / auto-approved / rejected | Requester | Outlook email with approver comments |
| Approved | Each supplier | Outlook purchase order email |
| Line without a supplier | Pantry admin | Outlook email |
| Daily 8 AM, items at or below minimum | Pantry admin | Outlook email with a table of low items |
| In-app actions | Current user | Success, warning and error toasts |

### Note 7: Tracking
**My requests** shows each request's progress (Submitted → Approved → Ordered → Received), its line items, and its full approval history. The **Receiving** screen adds delivered quantities back to the Pantry Items list.

## Demo script (about 10 minutes)
1. **SharePoint.** Open the Office Pantry site and show the five lists and the Pantry Items stock columns.
2. **Dashboard** (role: Requester). Show the KPIs, the "How it works" strip, and Needs restocking.
3. **New request.** Show the inventory-check note and that well-stocked items are disabled.
   - Add Sparkling Water 500ml (low stock; quantity defaults to its reorder quantity, 24 units, ₹960). The cart shows the green **Auto-approved** note.
   - Switch to **All items** and point out that Mineral Water (well stocked) can't be added.
   - Submit, then open **My requests**: within 1–2 minutes the tracker moves to Approved, then Ordered.
   - Show the supplier's email.
4. **New request** again. Add Coffee Beans Arabica 1kg (low stock) with quantity 5 (₹6,000). The cart shows the amber **Needs office manager approval** note.
   - Submit. Show the approval email in Outlook and click **Approve**.
   - Show the requester's email and the supplier's email.
5. Switch the role to **Approver**. Under **Approvals**, show the "Over ₹5,000" reason and reject a different request with a comment.
6. Switch the role to **Pantry Admin**. Under **Receiving**, mark the order received, then show that Current Stock went up in the SharePoint list.
7. **Copilot agent.** Ask the sample questions above.
8. Run the **Daily Low Stock Alert** flow manually and show the email.

The order flows check the Pantry Orders list once a minute, so allow 1–2 minutes between submitting and seeing the next status.
