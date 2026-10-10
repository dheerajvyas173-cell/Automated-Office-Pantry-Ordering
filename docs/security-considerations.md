# Security Considerations

## 1. Data Security

### Dataverse Security Model

| Layer | Implementation | Purpose |
|-------|---------------|---------|
| **Environment Security** | Dedicated Dataverse environment | Isolates pantry data from other business apps |
| **Table Permissions** | Security roles per table | Controls CRUD access by role |
| **Row-Level Security** | Owner-based access on SupplyOrders | Employees see only their own orders |
| **Column-Level Security** | Column security profiles on pricing fields | Hides supplier pricing from employees |
| **Field Masking** | Supplier email/phone partially masked for employees | Prevents unauthorized supplier contact |

### Security Roles

#### 1. Pantry Employee
```
PantryItems:        Read (Organization scope)
SupplyOrders:       Create, Read (User scope — own records only)
OrderLineItems:     Create, Read (User scope — via parent order)
Suppliers:          Read (Organization scope, limited columns)
ApprovalHistory:    Read (User scope — own orders only)
```

#### 2. Cafeteria Staff
```
PantryItems:        Read, Update (Organization scope)
SupplyOrders:       Create, Read, Update (Business Unit scope)
OrderLineItems:     Create, Read, Update (Business Unit scope)
Suppliers:          Read (Organization scope)
ApprovalHistory:    Read (Business Unit scope)
```

#### 3. Office Manager
```
All tables:         Full CRUD (Organization scope)
System Admin:       Environment settings access
```

### Data Loss Prevention (DLP)

Configure a DLP policy in the Power Platform Admin Center:

- **Business data group:** Dataverse, Office 365 Outlook, Approvals, Microsoft Teams
- **Non-business data group:** All other connectors
- **Blocked connectors:** Social media, external storage services

This ensures pantry data cannot flow to unauthorized external services.

---

## 2. Authentication & Authorization

### Power Apps Authentication
- **Method:** Azure Active Directory (AAD) / Entra ID
- **SSO:** Users authenticate via organizational SSO
- **Conditional Access:** Enforce MFA for app access (recommended)
- **Session Timeout:** 24-hour session with re-authentication

### Copilot Agent Authentication
- **Method:** Azure AD v2 with OAuth 2.0
- **Scopes:** Read access to Dataverse tables only
- **Token Refresh:** Automatic via Copilot Studio
- **Channel Security:** Teams channel restricts agent access to org members

### Power Automate Service Accounts
- **Approval Flow:** Runs under a service account with limited Dataverse permissions
- **Supplier Email:** Dedicated shared mailbox (pantryorders@company.com)
- **Principle of Least Privilege:** Each flow connection uses minimum required permissions

---

## 3. Network Security

### Power Platform Environment
- **Region:** Deploy in the same region as your Microsoft 365 tenant
- **IP Restrictions:** Configure tenant IP restrictions for Power Platform admin access
- **Virtual Network:** For premium environments, use VNet integration

### Email Security
- **Supplier Emails:** Sent from a verified organizational domain
- **SPF/DKIM/DMARC:** Ensure email authentication is configured
- **Email Content:** No sensitive data beyond order details in supplier emails

---

## 4. Data Privacy & Compliance

### Personal Data Handling
- **User Data Collected:** Name, email (from AAD — no manual entry)
- **Retention:** Order records retained for 2 years, then archived
- **Right to Erasure:** Admin can delete user's order history via Dataverse

### Audit Trail
- **Dataverse Auditing:** Enabled on all pantry tables
- **Tracks:** Create, Update, Delete operations with user identity and timestamp
- **Retention:** Audit logs retained per organizational policy
- **Access:** Only admins can view audit logs

### Compliance Features
- **Data residency:** Data stays within the tenant's geographic region
- **Encryption at rest:** Dataverse encrypts all data at rest (AES-256)
- **Encryption in transit:** All connections use TLS 1.2+
- **SOC 2 compliance:** Inherited from Microsoft Power Platform

---

## 5. Application Security

### Input Validation
- **Quantity Fields:** Validated as positive integers with upper bounds
- **Text Fields:** Maximum length enforced, no HTML/script injection risk (Power Apps handles this)
- **Currency Fields:** Validated format and reasonable ranges
- **Date Fields:** Cannot be set to past dates for orders

### Business Logic Security
- **Threshold Enforcement:** Approval thresholds enforced at both app level and flow level
- **Double Validation:** Order totals recalculated server-side in Power Automate, not trusted from the app
- **Status Transitions:** Business rules enforce valid status transitions only:
  ```
  Draft → Submitted → Pending Approval → Approved/Rejected
  Approved → Sent to Supplier → Delivered
  ```
- **Cannot Skip Approval:** If thresholds are met, status cannot be set to Approved without going through the approval flow

### Supplier Email Safety
- **Template-Based:** Emails use pre-defined HTML templates; user input is limited to quantity and notes
- **No File Attachments:** Orders are inline in the email body (no attachment-based attacks)
- **Reply Tracking:** Supplier replies go to a monitored shared mailbox

---

## 6. Monitoring & Alerting

### Power Platform Admin Center
- **Analytics:** Monitor app usage, flow runs, and errors
- **Alerts:** Configure alerts for:
  - Flow failures (approval timeouts, email send failures)
  - Unusual order patterns (spike in orders, high-value orders)
  - Authentication failures

### Recommended Monitors
| Monitor | Tool | Threshold |
|---------|------|-----------|
| Failed flow runs | Power Automate analytics | Any failure |
| Approval timeouts | Custom flow | > 72 hours |
| Large orders | Power Automate | > $1,000 |
| Repeated rejections | Custom flow | > 3 rejections by same user |
| Data export attempts | Dataverse audit | Any bulk export |

---

## 7. Deployment Security

### Environment Strategy
```
Development → Testing → Production
```

- **Development:** Maker environment for building and testing
- **Testing/UAT:** Separate environment with sample data
- **Production:** Managed solution deployment only

### Solution Management
- **Managed Solutions:** Deploy as managed solutions to production (prevents editing)
- **Version Control:** Export solution files to source control (Azure DevOps or GitHub)
- **Change Management:** All changes go through the dev → test → prod pipeline

### Environment Variables
Store configurable values as Environment Variables (not hard-coded):
- Budget threshold
- Quantity threshold
- Supplier email addresses
- Office manager email
- Teams channel IDs
