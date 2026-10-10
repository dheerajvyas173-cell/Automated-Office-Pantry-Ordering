# Pantry Supply Ordering - Setup Guide

## Quick Setup (Recommended)

Since Power Platform solutions can only be reliably created by exporting from an environment
(the XML format is an internal serialization, not a human-authoring format), use one of
these approaches to set up the system:

### Option A: Power Platform CLI (pac) - Automated

1. Install the Power Platform CLI: https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction
2. Authenticate: `pac auth create --environment https://your-org.crm.dynamics.com`
3. Run the setup script: `python setup/create_tables.py`

### Option B: Manual Setup in Maker Portal (15-20 minutes)

1. Go to https://make.powerapps.com
2. Create a new Solution named "Pantry Supply Ordering" with publisher prefix `cr`
3. Follow `setup/manual-setup-steps.md` to create all tables, columns, and relationships
4. Create Cloud Flows using the definitions in `power-automate/` docs
5. Build the Canvas App using the designs in `power-apps/` docs

### Option C: Dataverse Web API Script

1. Register an Azure AD app with Dataverse permissions
2. Update `setup/create_tables_webapi.ps1` with your environment URL
3. Run in PowerShell: `.\setup\create_tables_webapi.ps1`
