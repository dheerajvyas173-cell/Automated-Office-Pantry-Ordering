# Solution Architecture

## High-Level Architecture

The Automated Office Pantry Supply Ordering System is built entirely on the Microsoft Power Platform, leveraging Dataverse as the central data store, Power Apps for the user interface, Power Automate for workflow automation, and Copilot Studio for AI-powered assistance.

### Component Interaction Diagram

```
                    ┌─────────────────┐
                    │    Employees     │
                    │  (Power Apps)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Power Apps     │
                    │   Canvas App     │
                    │                  │
                    │ ┌──────────────┐ │
                    │ │ Request Form │ │
                    │ │  + Inventory │ │
                    │ │   Dashboard  │ │
                    │ └──────┬───────┘ │
                    └────────┼────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
     │   Dataverse    │ │  Power   │ │   Copilot    │
     │   Tables       │ │ Automate │ │   Studio     │
     │                │ │  Flows   │ │   Agent      │
     │ - PantryItems  │ │          │ │              │
     │ - SupplyOrders │ │ ┌──────┐ │ │ - NL Queries │
     │ - OrderLines   │ │ │Apprvl│ │ │ - Stock Info │
     │ - Suppliers    │ │ │ Flow │ │ │ - Order Hist │
     │ - ApprovalHist │ │ └──┬───┘ │ └──────────────┘
     └────────────────┘ │   │      │
                        │ ┌─▼────┐ │
                        │ │Email │ │
                        │ │ Flow │ │
                        │ └──┬───┘ │
                        │   │      │
                        │ ┌─▼────┐ │
                        │ │Alert │ │
                        │ │ Flow │ │
                        │ └──────┘ │
                        └──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
     │   Office       │ │ Supplier │ │   Microsoft  │
     │   Manager      │ │  Email   │ │   Teams      │
     │  (Approvals)   │ │          │ │ (Notifications│
     └────────────────┘ └──────────┘ └──────────────┘
```

## Data Flow

### 1. Order Submission Flow

```
Employee opens app
    → Selects items from PantryItems catalog
    → System checks current stock levels
    → If stock available: order submitted to SupplyOrders table
    → If below threshold: triggers approval flow
    → If within threshold: auto-approved, triggers supplier email
```

### 2. Approval Flow

```
Order exceeds threshold ($200 or 50 units)
    → Power Automate creates approval request
    → Office Manager receives Teams/Email notification
    → Manager approves or rejects
    → ApprovalHistory record created
    → If approved: supplier email sent
    → If rejected: requester notified with reason
```

### 3. Low Stock Alert Flow

```
Scheduled flow runs daily at 8:00 AM
    → Queries PantryItems where CurrentStock < ReorderPoint
    → For each low-stock item:
        → Sends Teams notification to cafeteria staff
        → Optionally auto-creates a supply order
```

## Security Architecture

### Dataverse Security Roles

| Role | Tables Access | Actions |
|------|-------------|---------|
| Employee | PantryItems (Read), SupplyOrders (Create, Read own) | Submit orders, view inventory |
| Cafeteria Staff | PantryItems (Read/Update), SupplyOrders (Full), Suppliers (Read) | Manage inventory, create orders |
| Office Manager | All tables (Full) | Approve orders, manage suppliers, configure thresholds |

### Data Security

- **Row-Level Security**: Employees see only their own orders
- **Column-Level Security**: Supplier pricing visible only to managers
- **Environment Security**: Solution deployed in a dedicated Dataverse environment
- **Audit Logging**: All changes tracked via Dataverse auditing

## Integration Points

| Integration | Method | Purpose |
|-------------|--------|---------|
| Outlook | Power Automate connector | Supplier order emails |
| Teams | Power Automate connector | Approval requests and notifications |
| Dataverse | Native Power Apps connector | Data storage and retrieval |
| Copilot Studio | Dataverse plugin | AI-powered queries |

## Scalability Considerations

1. **Multi-Office Support**: Add an `Office` table and filter all queries by office location
2. **Multiple Suppliers**: Supplier table supports multiple vendors per item category
3. **Budget Tracking**: Add monthly/quarterly budget tables for department-level tracking
4. **Barcode Scanning**: Power Apps camera control can scan barcodes for quick inventory updates
5. **Power BI Integration**: Connect Dataverse tables to Power BI for advanced analytics dashboards
