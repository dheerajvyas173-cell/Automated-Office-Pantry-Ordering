# Presentation Guide

## Recommended Structure (20-25 minutes)

---

## 1. Introduction & Problem Statement (2 minutes)

### Talking Points:
- Office pantry management is typically manual — sticky notes, emails, spreadsheets
- Pain points: items run out, no visibility into stock, slow approval processes, no spending tracking
- Goal: automate the entire process from request to delivery with AI-powered insights

### Opening Statement (Example):
> "We've all experienced the frustration of going to the office pantry for coffee only to find it's out of stock. This solution eliminates that problem by automating inventory tracking, ordering, approvals, and restocking — all within the Microsoft Power Platform."

---

## 2. Architecture Walkthrough (3 minutes)

### Talking Points:
- Show the architecture diagram from the README
- Explain each component and why it was chosen:
  - **Dataverse** over SharePoint: Relational data model, security roles, calculated columns, business rules — better suited for structured inventory data than list-based SharePoint
  - **Power Apps Canvas App**: Flexible UI design, works on tablet and mobile
  - **Power Automate Cloud Flows**: Native integration with Approvals, Outlook, Teams
  - **Copilot Studio**: Pre-built AI capabilities with Dataverse knowledge grounding
- Explain data flow: Request → Validation → Approval → Supplier → Delivery → Inventory Update
- Note: All components are within the Microsoft ecosystem — no external dependencies

### Key Architecture Decision:
> "I chose Dataverse over SharePoint for data storage because it provides relational table support, row-level security, calculated columns, and business rules — features essential for an inventory system. SharePoint lists work well for documents but lack the data integrity features needed here."

---

## 3. Live Demo (12-15 minutes)

### Demo Script:

#### Part A: Power Apps — Submit an Order (4 minutes)
1. Open the Pantry Supply Manager app
2. Show the **Home Screen**: point out low stock alerts and recent orders
3. Navigate to **Inventory Dashboard**: show KPI cards, stock levels by category
4. Navigate to **New Order**:
   - Filter by "Coffee" category
   - Point out stock level indicators (green/yellow/red)
   - Add Nespresso Lungo Pods × 200 (to trigger approval)
   - Add Ground Coffee × 10
   - Show the order summary: total $162.50, 210 units
   - Point out the approval indicator: "This order exceeds thresholds and will require manager approval"
   - Submit the order
5. Show the order in **Order History** as "Pending Approval"

#### Part B: Power Automate — Approval Workflow (3 minutes)
1. Switch to Teams or Outlook
2. Show the approval request with the formatted HTML summary
3. Point out: order number, requester, item table, reason for approval
4. **Approve** the order with a comment
5. Switch back to Power Apps — show status updated to "Approved"
6. Show the supplier email that was automatically generated
7. Point out the formatted order with delivery instructions

#### Part C: Power Automate — Low Stock Alert (2 minutes)
1. Show a sample low stock alert email (or trigger the flow manually)
2. Show the Teams adaptive card notification
3. Point out severity levels: Out of Stock, Critical, Low
4. Show the "Open Pantry Manager" action button on the card

#### Part D: Copilot Agent — AI Assistant (3 minutes)
1. Open the Copilot agent in Teams
2. Ask: **"How many coffee pods are left?"**
   - Show the structured response with stock levels
3. Ask: **"Which items are running low?"**
   - Show the low stock report
4. Ask: **"When was the last order placed?"**
   - Show the order history response
5. Ask: **"Who supplies our coffee?"**
   - Show supplier contact details
6. Point out: "The agent understands natural language and queries live Dataverse data"

#### Part E: Small Order — Auto-Approval (1 minute)
1. Create a small order: Sugar × 5 ($12.50)
2. Submit — show it's auto-approved (no manager intervention needed)
3. Show supplier email sent automatically
4. "Orders under $200 and 50 units skip the approval step entirely"

---

## 4. Technical Decisions & Integrations (3 minutes)

### Talking Points:

#### Why Dataverse over SharePoint?
- Relational data model (tables with foreign keys)
- Row-level security (employees see only their orders)
- Calculated and rollup columns (stock status, order totals)
- Business rules (threshold enforcement server-side)
- Better performance for queries and aggregations
- Native Copilot Studio integration for AI queries

#### Why Canvas App over Model-Driven?
- Full control over UI/UX design
- Better for employee-facing apps (simpler, more intuitive)
- Custom layouts for the inventory dashboard
- Easy category filtering and visual stock indicators
- Model-driven would be better for admin/back-office use

#### Security Approach
- Three security roles: Employee, Cafeteria Staff, Manager
- Row-level security on orders (employees see only their own)
- Column-level security on pricing (hidden from employees)
- DLP policies prevent data flowing to unauthorized connectors
- All emails sent from organizational shared mailbox

#### Approval Logic
- Dual threshold: budget ($200) AND quantity (50 units) — configurable
- Approval enforced at both app level (UI indicator) and flow level (cannot bypass)
- 72-hour timeout with escalation
- Full audit trail in ApprovalHistory table

---

## 5. Improvements & Scalability (3 minutes)

### Short-Term Improvements
1. **Power BI Dashboard**: Connect Dataverse tables for advanced analytics — spending trends, top-ordered items, supplier performance
2. **Barcode Scanning**: Use Power Apps camera control to scan item barcodes for quick inventory updates during restocking
3. **Recurring Orders**: Allow cafeteria staff to set up weekly/monthly recurring orders for staple items
4. **Budget Management**: Add monthly/quarterly budget limits per department with automatic enforcement

### Medium-Term Scalability
1. **Multi-Office Support**: Add an Office/Location table, filter all data by location, support cross-office ordering
2. **Supplier Portal**: Create a separate model-driven app for suppliers to confirm orders, update delivery dates, and submit invoices
3. **Mobile App**: Publish the Power App for mobile devices — cafeteria staff can do inventory checks while walking through the pantry
4. **Integration with ERP**: Connect to finance systems (SAP, Oracle) for invoice reconciliation and budget tracking

### Advanced Features
1. **Predictive Ordering**: Use AI Builder to predict reorder timing based on consumption patterns
2. **Power Automate Desktop**: Automate supplier website ordering for suppliers without email-based ordering
3. **QR Code Labels**: Generate and print QR codes for shelves that link directly to the reorder form for that item
4. **Environmental Dashboard**: Track sustainability metrics (packaging waste, local sourcing percentages)

---

## 6. Q&A (2-3 minutes)

### Anticipated Questions & Answers:

**Q: How do you handle concurrent orders for the same item?**
> A: Dataverse handles record-level locking. The stock check at order time is informational — actual stock updates happen only when orders are marked as delivered. Multiple orders for the same item can exist simultaneously.

**Q: What happens if the approval flow fails or times out?**
> A: There's a 72-hour timeout. After that, the order escalates to a backup approver. If the flow itself errors, it's configured with retry logic (3 retries) and sends an admin notification on persistent failure.

**Q: Can this work with SharePoint instead of Dataverse?**
> A: Yes, but with trade-offs. SharePoint lacks row-level security, calculated columns, and relationships. You'd need to manage security via Power Apps logic and use Power Automate for calculations, making the solution more fragile and harder to maintain.

**Q: How would you deploy this across multiple offices?**
> A: Add a Location table and associate each PantryItem and SupplyOrder with a location. Filter all galleries and flows by the user's assigned location. The core solution architecture remains the same.

**Q: What are the licensing costs?**
> A: Power Apps per-user license ($20/user/month) or per-app ($5/app/user/month). Power Automate is included with most M365 plans for standard flows; premium connectors require per-user plan ($15/user/month). Copilot Studio is $200/month per 25,000 messages. For a typical office of 50 employees, the monthly cost would be approximately $250-$450.

---

## Demo Checklist

Before the presentation:

- [ ] Dataverse tables created with sample data loaded
- [ ] Power Apps published and accessible
- [ ] All three Power Automate flows turned on and tested
- [ ] Copilot Agent deployed to Teams
- [ ] Test all five demo scenarios end-to-end
- [ ] Prepare fallback screenshots in case of connectivity issues
- [ ] Clear any test approval notifications from inbox
- [ ] Set the manager approver to your own email for live demo
- [ ] Have the architecture diagram ready to screen-share
