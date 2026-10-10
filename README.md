# Automated Office Pantry Supply Ordering System

A Microsoft Power Platform solution for streamlining office cafeteria supply ordering, inventory tracking, approval workflows, and AI-powered supply insights.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Power Platform Solution                       │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │  Power Apps   │───▶│  Power Automate   │───▶│  Outlook / Teams  │  │
│  │  Canvas App   │    │  Cloud Flows      │    │  Notifications    │  │
│  │              │    │                    │    │                   │  │
│  │  - Request    │    │  - Approval Flow   │    │  - Approval Req   │  │
│  │    Form       │    │  - Supplier Email  │    │  - Status Updates │  │
│  │  - Inventory  │    │  - Low Stock Alert │    │  - Low Stock Alert│  │
│  │    Dashboard  │    │  - Scheduled Check │    │                   │  │
│  │  - Order      │    │                    │    │                   │  │
│  │    History    │    │                    │    │                   │  │
│  └──────┬───────┘    └────────┬───────────┘    └───────────────────┘  │
│         │                     │                                       │
│         ▼                     ▼                                       │
│  ┌──────────────────────────────────────────┐                        │
│  │            Dataverse Tables               │                        │
│  │                                           │                        │
│  │  - PantryItems (Inventory)                │                        │
│  │  - SupplyOrders (Orders)                  │                        │
│  │  - OrderLineItems (Order Details)         │                        │
│  │  - Suppliers (Supplier Info)              │                        │
│  │  - ApprovalHistory (Audit Trail)          │                        │
│  └──────────────────────────────────────────┘                        │
│                                                                      │
│  ┌──────────────────────────────────────────┐                        │
│  │         Copilot Studio Agent              │                        │
│  │                                           │                        │
│  │  - Stock level queries                    │                        │
│  │  - Reorder date lookups                   │                        │
│  │  - Supplier detail retrieval              │                        │
│  │  - Natural language inventory search      │                        │
│  └──────────────────────────────────────────┘                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Solution Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Supply Request App | Power Apps (Canvas) | Employee-facing form for ordering supplies |
| Inventory Dashboard | Power Apps (Canvas) | Real-time inventory levels and analytics |
| Approval Workflow | Power Automate (Cloud Flow) | Route high-value orders for manager approval |
| Supplier Ordering | Power Automate (Cloud Flow) | Auto-generate supplier emails on approval |
| Low Stock Alerts | Power Automate (Scheduled Flow) | Daily inventory checks with notifications |
| Supply Assistant | Copilot Studio Agent | AI-powered stock insights and queries |
| Data Layer | Dataverse | Centralized data storage with security |

## Quick Start

See the [Implementation Guide](docs/implementation-guide.md) for step-by-step setup instructions.

## Project Structure

```
├── README.md                          # This file
├── docs/
│   ├── implementation-guide.md        # Step-by-step setup instructions
│   ├── architecture.md                # Detailed architecture documentation
│   ├── security-considerations.md     # Security and compliance details
│   └── presentation-guide.md         # Interview presentation outline
├── dataverse/
│   ├── tables.md                      # Table schemas and relationships
│   └── sample-data.md                 # Sample data for testing
├── power-apps/
│   ├── app-design.md                  # Screen layouts and navigation
│   └── formulas.md                    # Power Fx formulas reference
├── power-automate/
│   ├── approval-flow.md               # Approval workflow definition
│   ├── supplier-order-flow.md         # Supplier email automation
│   └── low-stock-alert-flow.md        # Scheduled inventory check flow
└── copilot-agent/
    ├── agent-config.md                # Copilot Studio agent setup
    └── topics.md                      # Conversation topics and triggers
```

## Key Features

- **Inventory-Aware Ordering**: Real-time stock checks prevent over-ordering
- **Configurable Thresholds**: Budget and quantity limits trigger approvals
- **Automated Supplier Communication**: Approved orders generate formatted supplier emails
- **AI Assistant**: Natural language queries for stock levels, order history, and supplier info
- **Low Stock Alerts**: Proactive notifications when items reach reorder points
- **Full Audit Trail**: Complete order history with approval records
- **Role-Based Access**: Dataverse security roles for employees, managers, and admins

## Thresholds (Configurable)

| Parameter | Default Value |
|-----------|--------------|
| Budget approval threshold | $200 |
| Quantity approval threshold | 50 units |
| Low stock alert threshold | 20% of max stock |
| Order check frequency | Daily at 8:00 AM |
