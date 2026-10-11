# Implementation Guide

## Prerequisites

- Microsoft 365 Business or Enterprise license
- Power Apps per-user or per-app plan
- Power Automate per-user plan (for approval flows)
- Copilot Studio license (for the AI agent)
- Dataverse environment provisioned
- Admin access to Power Platform Admin Center

---

## Phase 1: Environment & Data Setup (Day 1)

### Step 1.1: Create Dataverse Environment

1. Go to [Power Platform Admin Center](https://admin.powerplatform.microsoft.com)
2. **Environments** → **New**
3. Settings:
   - Name: `Pantry Ordering - Production`
   - Type: Production
   - Region: Your region
   - Enable Dataverse: Yes
   - Enable D365 apps: No
   - Security group: Your organization's security group
4. Click **Save**

### Step 1.2: Create Solution

1. Open [make.powerapps.com](https://make.powerapps.com)
2. Select the new environment
3. **Solutions** → **New solution**
4. Settings:
   - Display name: `Pantry Supply Ordering`
   - Publisher: Create new or use existing
   - Version: `1.0.0.0`

### Step 1.3: Create Dataverse Tables

Follow the schemas in [dataverse/tables.md](../dataverse/tables.md).

**Create tables in this order (due to relationships):**

1. **Suppliers** table
   - Add all columns as defined
   - Set `cr_name` as the primary column

2. **PantryItems** table
   - Add all columns
   - Create lookup to Suppliers (Preferred Supplier)
   - Add the calculated column for Stock Status
   - Add business rule for stock status updates

3. **SupplyOrders** table
   - Add all columns
   - Create lookups: RequestedBy (User), ApprovedBy (User), Supplier
   - Add business rules for approval threshold logic

4. **OrderLineItems** table
   - Add all columns
   - Create lookups: Order (SupplyOrders), PantryItem (PantryItems)
   - Add calculated column for LineTotal

5. **ApprovalHistory** table
   - Add all columns
   - Create lookups: Order (SupplyOrders), ActionBy (User)

### Step 1.4: Configure Security Roles

1. In the solution, **New** → **Security** → **Security role**
2. Create three roles as defined in [security-considerations.md](security-considerations.md):
   - Pantry Employee
   - Cafeteria Staff
   - Office Manager
3. Assign roles to users via **Admin Center** → **Environments** → **Security roles**

### Step 1.5: Import Sample Data

1. Prepare Excel files matching the sample data in [dataverse/sample-data.md](../dataverse/sample-data.md)
2. In Dataverse, for each table:
   - Open the table → **Import** → **Import data**
   - Map columns and import
3. Or use the Dataverse Web API / Power Automate to bulk-insert records

---

## Phase 2: Build Power Apps (Day 1-2)

### Step 2.1: Create Canvas App

1. In the solution, **New** → **App** → **Canvas app**
2. Name: `Pantry Supply Manager`
3. Format: Tablet
4. Add Dataverse as data source (all 5 tables)

### Step 2.2: Build Screens

Follow the designs in [power-apps/app-design.md](../power-apps/app-design.md):

#### Screen 1: Home Screen
1. Add a header with app title and user info
2. Create a gallery for low stock alerts
3. Create a gallery for recent orders
4. Add navigation buttons (New Order, My Orders, Dashboard)

#### Screen 2: New Order Screen
1. Add category dropdown filter
2. Create items gallery with stock level indicators
3. Add quantity input and "Add to Order" button
4. Create order summary section with collection display
5. Add approval threshold indicator
6. Add Submit and Cancel buttons
7. Implement all formulas from [power-apps/formulas.md](../power-apps/formulas.md)

#### Screen 3: Order History Screen
1. Add status and date filters
2. Create orders gallery with status icons
3. Add detail view for selected order

#### Screen 4: Inventory Dashboard
1. Add KPI cards (Total Items, Low Stock, Out of Stock)
2. Create stock level visualization by category
3. Add low stock items gallery with quick-order buttons

### Step 2.3: Configure App OnStart

Add the OnStart formula from [power-apps/formulas.md](../power-apps/formulas.md):
- Set user context
- Set threshold variables
- Initialize order collection

### Step 2.4: Test the App

1. **Play** the app in Power Apps Studio
2. Test each screen's navigation
3. Test order submission with quantities under thresholds (auto-approve)
4. Test order submission with quantities over thresholds (should set status to Pending)
5. Verify data is written correctly to Dataverse
6. Test input validation (negative quantities, empty orders)

---

## Phase 3: Build Power Automate Flows (Day 2-3)

### Step 3.1: Approval Workflow

Follow [power-automate/approval-flow.md](../power-automate/approval-flow.md):

1. Create new **Automated cloud flow**
2. Trigger: When a row is added or modified (Dataverse - SupplyOrders)
3. Add filter: `cr_orderstatus eq 3`
4. Add steps:
   - Get order details (expand requestedby)
   - List line items (expand pantryitem)
   - Compose HTML summary
   - Start and wait for approval
   - Condition branch: Approved vs Rejected
   - Update order status
   - Create approval history record
   - Send notification email
5. Configure error handling (run-after settings)
6. Set approval timeout to 72 hours
7. **Save** and **Turn on** the flow

### Step 3.2: Supplier Order Email

Follow [power-automate/supplier-order-flow.md](../power-automate/supplier-order-flow.md):

1. Create new **Automated cloud flow**
2. Trigger: When order status changes to Approved (status = 4) and email not sent
3. Add steps:
   - Get order with supplier details
   - List line items with item names
   - Create HTML table of items
   - Compose formatted supplier email
   - Send email via Outlook
   - Update order (email sent = true, status = Sent to Supplier)
   - Notify requester via Teams
4. **Save** and **Turn on**

### Step 3.3: Low Stock Alert

Follow [power-automate/low-stock-alert-flow.md](../power-automate/low-stock-alert-flow.md):

1. Create new **Scheduled cloud flow**
2. Schedule: Daily at 8:00 AM
3. Add steps:
   - Query PantryItems below reorder point
   - Condition: any items found?
   - Categorize by severity (Out of Stock / Critical / Low)
   - Build HTML alert table
   - Send email to cafeteria staff and manager
   - Post Teams adaptive card
   - Optionally auto-create draft order for out-of-stock items
4. **Save** and **Turn on**

### Step 3.4: Test All Flows

1. **Approval Flow:**
   - Create an order exceeding $200 in Power Apps
   - Verify approval request arrives in Teams/Outlook
   - Approve it → verify status updates and supplier email triggers
   - Create another → Reject it → verify rejection notification

2. **Supplier Email:**
   - After approving an order, verify formatted email sent to supplier address
   - Check order status updated to "Sent to Supplier"
   - Check Teams notification sent to requester

3. **Low Stock Alert:**
   - Manually set an item's stock below its reorder point
   - Trigger the flow manually (click **Test** → **Manually**)
   - Verify email and Teams notification received
   - Verify correct severity categorization

---

## Phase 4: Build Copilot Agent (Day 3)

### Step 4.1: Create Agent

Follow [copilot-agent/agent-config.md](../copilot-agent/agent-config.md):

1. Go to [Copilot Studio](https://copilotstudio.microsoft.com)
2. Create new agent: "Pantry Supply Assistant"
3. Set the system instructions
4. Configure authentication (Azure AD v2)

### Step 4.2: Add Knowledge Sources

1. Add Dataverse tables as knowledge:
   - PantryItems
   - SupplyOrders
   - OrderLineItems
   - Suppliers
2. Configure table descriptions and column descriptions
3. Set access permissions (read-only)

### Step 4.3: Create Topics

Follow [copilot-agent/topics.md](../copilot-agent/topics.md):

For each topic:
1. **New topic** → Add trigger phrases
2. Create the conversation flow with question nodes and action nodes
3. Add Dataverse queries via "Call an action" nodes
4. Configure response messages with dynamic data
5. Test each topic individually

### Step 4.4: Create Supporting Flows

Build the Power Automate flows that the agent calls:
1. Get Stock Summary flow
2. Get Order History flow
3. Get Supplier Details flow

Register these as plugin actions in Copilot Studio.

### Step 4.5: Deploy to Teams

1. **Channels** → **Microsoft Teams** → **Turn on Teams**
2. Install the agent in the Cafeteria Staff channel
3. Test by chatting with the agent in Teams

### Step 4.6: Test Agent

Run through all test queries from [dataverse/sample-data.md](../dataverse/sample-data.md#copilot-agent-test-queries):

1. "How many coffee pods are left?"
2. "When was the last order placed?"
3. "Which items are running low?"
4. "What's the contact info for our coffee supplier?"
5. "How much did we spend on snacks last month?"
6. Test fallback: "What's the weather today?" → should gracefully decline

---

## Phase 5: Integration Testing (Day 3-4)

### End-to-End Test Scenarios

#### Scenario 1: Small Order (Auto-Approved)
1. Open Power Apps → New Order
2. Add: Coffee Pods ×20, Sugar ×2 (Total: $20.00)
3. Submit → Should auto-approve (under thresholds)
4. Verify: Supplier email sent
5. Verify: Order appears in Order History as "Sent to Supplier"
6. Ask Copilot: "What's the status of my latest order?"

#### Scenario 2: Large Order (Requires Approval)
1. Open Power Apps → New Order
2. Add: Coffee Pods ×200, Tea ×50 (Total: $192.50, Qty: 250)
3. Submit → Should go to Pending Approval
4. Verify: Approval request sent to manager
5. Manager approves → Verify supplier email sent
6. Manager rejects → Verify rejection notification

#### Scenario 3: Low Stock Alert
1. Set Green Tea stock to 2 (below reorder point of 3)
2. Trigger low stock flow
3. Verify: Email and Teams notification with correct severity
4. Ask Copilot: "Which items are running low?" → Should include Green Tea

#### Scenario 4: Full Cycle
1. Copilot: "Which items are running low?" → Note items
2. Power Apps: Create order for low-stock items
3. Approval (if needed) → Approve
4. Supplier email sent
5. Mark order as delivered
6. Verify stock levels updated
7. Copilot: "When was the last order placed?" → Shows this order

---

## Phase 6: Deployment (Day 4)

### Export Solution
1. In make.powerapps.com → Solutions
2. Select the Pantry Supply Ordering solution
3. **Export** → **Managed** (for production)
4. Save the .zip file

### Import to Production
1. Switch to the production environment
2. **Solutions** → **Import**
3. Upload the managed solution .zip
4. Configure connection references (Dataverse, Outlook, Teams, Approvals)
5. Set environment variables (thresholds, email addresses)
6. Activate all flows
7. Share the app with appropriate security groups

### Post-Deployment
1. Assign security roles to users
2. Share the Power App URL / add to Teams tab
3. Announce the agent in the Cafeteria Staff Teams channel
4. Provide a brief user training session
5. Monitor for 1 week for any issues
