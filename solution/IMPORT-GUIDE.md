# Power Platform Solution Import Guide

## Pantry Supply Ordering System - v1.0.0.0

### Prerequisites
- Power Platform environment with Dataverse database provisioned
- System Administrator or System Customizer security role
- Power Automate premium license (for Dataverse triggers)
- Microsoft 365 license (for Outlook and Teams connectors)

---

### Step 1: Prepare the Solution ZIP

The `solution/` directory contains the unmanaged solution components. To create an importable ZIP:

1. Select all files and folders inside the `solution/` directory:
   - `[Content_Types].xml`
   - `solution.xml`
   - `customizations.xml`
   - `Workflows/` (folder with 3 flow JSON files)
   - `CanvasApps/` (folder with app source)
2. Compress them into a single ZIP file named `PantrySupplyOrdering_1_0_0_0.zip`

**Important:** The ZIP must contain the files at the root level, NOT inside a subfolder.

---

### Step 2: Import the Solution

1. Go to [Power Apps Maker Portal](https://make.powerapps.com)
2. Select your target environment
3. Navigate to **Solutions** in the left menu
4. Click **Import solution**
5. Click **Browse** and select `PantrySupplyOrdering_1_0_0_0.zip`
6. Click **Next**
7. Review the solution components
8. Click **Import**
9. Wait for the import to complete (may take 2-5 minutes)

---

### Step 3: Configure Connection References

After import, you need to set up connection references for the flows:

1. In the imported solution, find the **Cloud Flows**
2. Edit each flow and configure these connections:
   - **Microsoft Dataverse** - Sign in with your org account
   - **Approvals** - Sign in (auto-configured with your account)
   - **Office 365 Outlook** - Sign in for email sending
   - **Microsoft Teams** - Sign in for Teams notifications

---

### Step 4: Configure Environment Variables

1. In the solution, go to **Environment Variables**
2. Update these values for your organization:

| Variable | Default | Description |
|----------|---------|-------------|
| Budget Approval Threshold | 200 | Orders above this $ amount require approval |
| Quantity Approval Threshold | 50 | Orders above this quantity require approval |
| Approver Email | officemanager@company.com | **Change to your approver's email** |
| Low Stock Alert Recipients | (empty) | **Set to comma-separated email addresses** |

---

### Step 5: Load Sample Data

1. Go to **Dataverse** > **Tables** in the maker portal
2. For each table, use **Import data from Excel** or manually enter records:
   - Import `SampleData/Suppliers.csv` into the **Suppliers** table first
   - Import `SampleData/PantryItems.csv` into the **Pantry Items** table second
     (set the Preferred Supplier lookup column manually after import)

**Tip:** You can also use the Power Apps data import wizard or Power Automate to bulk-load the CSV files.

---

### Step 6: Set Up Security Roles

Create three security roles in your environment:

#### 1. Pantry User
- **Pantry Items**: Read (Organization)
- **Supply Orders**: Create, Read own, Write own
- **Order Line Items**: Create, Read own, Write own
- **Suppliers**: Read (Organization)
- **Approval History**: Read own

#### 2. Pantry Manager
- All Pantry User permissions, plus:
- **Supply Orders**: Read all, Write all
- **Order Line Items**: Read all
- **Approval History**: Create, Read all, Write all
- **Pantry Items**: Write (Organization)

#### 3. Pantry Admin
- Full access to all pantry tables

---

### Step 7: Turn On Cloud Flows

1. In the solution, navigate to **Cloud Flows**
2. Turn on each flow:
   - **Pantry Order Approval** - Triggers when order status = Pending Approval
   - **Supplier Order Email** - Triggers when order status = Approved
   - **Daily Low Stock Alert** - Runs daily at 8:00 AM UTC

---

### Step 8: Build the Canvas App

The `CanvasApps/` directory contains the app source definition with all screen layouts, formulas, and data connections. To recreate:

1. Go to **Power Apps** > **Apps** > **+ New app** > **Canvas**
2. Choose **Tablet** layout (1366x768)
3. Add Dataverse data sources: PantryItems, SupplyOrders, OrderLineItems, Suppliers, ApprovalHistory
4. Create 4 screens following the JSON definitions in `CanvasApps/cr_PantrySupplyManager_src/Screens/`:
   - **ScrHome** - Dashboard with navigation, low stock alerts, recent orders
   - **ScrNewOrder** - Item catalog with cart, order submission
   - **ScrOrderHistory** - Filterable order list with status tracking
   - **ScrDashboard** - Inventory KPIs, stock level bars, quick reorder
5. Copy Power Fx formulas from the JSON files for each control's properties
6. Set the App.OnStart formula from `App.json`

---

### Step 9: Set Up Copilot Agent (Optional)

1. Go to [Copilot Studio](https://copilotstudio.microsoft.com)
2. Create a new agent named **Pantry Supply Assistant**
3. Add Dataverse knowledge sources: PantryItems, SupplyOrders, Suppliers
4. Configure topics from `copilot-agent/topics.md`
5. Deploy to Microsoft Teams

---

### Post-Import Checklist

- [ ] Solution imported successfully
- [ ] All 5 Dataverse tables created (Suppliers, Pantry Items, Supply Orders, Order Line Items, Approval History)
- [ ] 6 global option sets created
- [ ] 4 environment variables configured with real values
- [ ] Connection references configured for all 3 flows
- [ ] All 3 cloud flows turned on
- [ ] Sample data loaded
- [ ] Security roles created and assigned
- [ ] Canvas app created and published
- [ ] Test order submitted and approval flow triggered
- [ ] Supplier email sent for approved order
- [ ] Low stock alert flow tested

---

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Import fails with "publisher not found" | The publisher `PantryDev` with prefix `cr` is included in the solution and will be created automatically |
| Flows fail to turn on | Ensure all connection references are configured first |
| Approval flow not triggering | Verify the order status is set to "Pending Approval" (100000002) |
| Supplier email not sending | Check that `cr_supplieremailsent` is `false` on the order record |
| Canvas app data not loading | Ensure the Dataverse connection is authenticated in the app |
