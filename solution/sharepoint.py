"""SharePoint data model: the five pantry lists, and the flow that creates them.

The lists live on one SharePoint site, set by the solution's environment variable
cr_PantrySiteUrl. The "Pantry - Create SharePoint site and lists" flow creates the site (if it
doesn't exist), the lists, their columns and the sample data, so nothing is set up by hand.
"""
import csv
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "sample-data")

SITE_URL = "https://dheerajvyas173gmail.sharepoint.com/sites/OfficePantry"
SITE_TITLE = "Office Pantry"
SITE_VAR = "cr_PantrySiteUrl"
SITE_PARAM = f"Pantry SharePoint site ({SITE_VAR})"
SITE = f"@parameters('{SITE_PARAM}')"

SUPPLIERS, ITEMS, ORDERS, LINES, HISTORY = (
    "Pantry Suppliers", "Pantry Items", "Pantry Orders", "Pantry Order Lines", "Pantry Approval History")

ITEM_CATEGORIES = ["Beverages", "Snacks", "Coffee & Tea", "Dairy", "Fruits", "Cleaning Supplies",
                   "Paper Products", "Kitchen Supplies", "Other"]
UNITS = ["Each", "Pack", "Box", "Case", "Bag", "Bottle", "Carton", "Roll", "Kg"]
ORDER_STATUSES = ["Draft", "Submitted", "Approved", "Rejected", "Ordered", "Partially Received", "Received",
                  "Cancelled"]
APPROVAL_STATUSES = ["Pending", "Approved", "Rejected"]
APPROVAL_ACTIONS = ["Submitted", "Approved", "Rejected", "Cancelled"]
SUPPLIER_CATEGORIES = ["Food & Beverage", "Office Supplies", "Cleaning Products", "Kitchen Equipment",
                       "Paper Products", "General"]


# Column definitions: (internal name, display name, type, options). The internal names have no
# spaces, so flows and REST calls can use them directly; Power Apps shows the display names.
def text(name, display, length=255):
    return (name, display, "Text", {"MaxLength": length})


def note(name, display):
    return (name, display, "Note", {})


def number(name, display, decimals=0):
    return (name, display, "Number", {"Decimals": decimals})


def choice(name, display, values):
    return (name, display, "Choice", {"choices": values})


def date(name, display, with_time=False):
    return (name, display, "DateTime", {"Format": "DateTime" if with_time else "DateOnly"})


def lookup(name, display, target):
    return (name, display, "Lookup", {"target": target})


LISTS = [
    (SUPPLIERS, "Suppliers of pantry supplies and their contact details", [
        text("ContactPerson", "Contact Person"), text("Email", "Email"), text("Phone", "Phone"),
        note("Address", "Address"), text("Website", "Website"),
        choice("SupplierCategory", "Category", SUPPLIER_CATEGORIES), note("Notes", "Notes"),
    ]),
    (ITEMS, "Pantry inventory: one row per item, with stock levels", [
        text("SKU", "SKU", 50), choice("Category", "Category", ITEM_CATEGORIES),
        choice("Unit", "Unit of Measure", UNITS), number("CurrentStock", "Current Stock"),
        number("MinimumStock", "Minimum Stock Level"), number("ReorderQuantity", "Reorder Quantity"),
        number("UnitPrice", "Unit Price", 2), lookup("PreferredSupplier", "Preferred Supplier", SUPPLIERS),
        text("StorageLocation", "Storage Location"), note("ItemDescription", "Description"),
    ]),
    (ORDERS, "Supply requests and their approval status (Title is the order number)", [
        choice("OrderStatus", "Order Status", ORDER_STATUSES),
        choice("ApprovalStatus", "Approval Status", APPROVAL_STATUSES),
        date("OrderDate", "Order Date"), date("RequiredByDate", "Required By Date"),
        date("ApprovalDate", "Approval Date", with_time=True), number("TotalAmount", "Total Amount", 2),
        text("RequestedBy", "Requested By"), text("RequesterName", "Requester Name"),
        text("ApprovedBy", "Approved By"), note("Justification", "Justification"),
        note("ApproverComments", "Approver Comments"), text("DeliveryAddress", "Delivery Address"),
    ]),
    (LINES, "Items on each supply order (Title is the item name)", [
        lookup("SupplyOrder", "Supply Order", ORDERS), lookup("PantryItem", "Pantry Item", ITEMS),
        lookup("Supplier", "Supplier", SUPPLIERS), number("Quantity", "Quantity"),
        number("UnitPrice", "Unit Price", 2), number("TotalCost", "Total Cost", 2),
    ]),
    (HISTORY, "Audit trail of every submission and approval decision", [
        lookup("SupplyOrder", "Supply Order", ORDERS), choice("ApprovalAction", "Action", APPROVAL_ACTIONS),
        text("Approver", "Approver"), date("ActionDate", "Action Date", with_time=True),
        note("Comments", "Comments"), choice("PreviousStatus", "Previous Status", APPROVAL_STATUSES),
        choice("NewStatus", "New Status", APPROVAL_STATUSES),
    ]),
]


def key(list_title):
    return list_title.replace(" ", "")


def field_xml(name, display, type_, opts):
    """SchemaXml for CreateFieldAsXml. Lookup targets are filled in by the flow at run time."""
    attrs = f'Type="{type_}" DisplayName="{escape(display)}" Name="{name}" StaticName="{name}"'
    if type_ == "Text":
        return f'<Field {attrs} MaxLength="{opts["MaxLength"]}" />'
    if type_ == "Note":
        return f'<Field {attrs} NumLines="6" RichText="FALSE" />'
    if type_ == "Number":
        return f'<Field {attrs} Decimals="{opts["Decimals"]}" />'
    if type_ == "DateTime":
        return f'<Field {attrs} Format="{opts["Format"]}" />'
    if type_ == "Choice":
        values = "".join(f"<CHOICE>{escape(v)}</CHOICE>" for v in opts["choices"])
        return f'<Field {attrs} Format="Dropdown"><CHOICES>{values}</CHOICES></Field>'
    if type_ == "Lookup":
        target = f"@{{variables('{key(opts['target'])}Id')}}"
        return f'<Field {attrs} List="{{{target}}}" ShowField="Title" />'
    raise ValueError(type_)


def sample_suppliers():
    with open(os.path.join(SAMPLE, "1_Suppliers.csv"), encoding="utf-8") as f:
        return [{"Title": r["Supplier Name"], "ContactPerson": r["Contact Person"], "Email": r["Email"],
                 "Phone": r["Phone"], "Address": r["Address"], "Website": r["Website"],
                 "SupplierCategory": r["Category"], "Notes": r["Notes"]} for r in csv.DictReader(f)]


def sample_items():
    with open(os.path.join(SAMPLE, "2_PantryItems.csv"), encoding="utf-8") as f:
        return [{"Title": r["Item Name"], "SKU": r["SKU"], "Category": r["Category"], "Unit": r["Unit of Measure"],
                 "CurrentStock": int(r["Current Stock"]), "MinimumStock": int(r["Minimum Stock Level"]),
                 "ReorderQuantity": int(r["Reorder Quantity"]), "UnitPrice": float(r["Unit Price"]),
                 "StorageLocation": r["Storage Location"], "ItemDescription": r["Description"],
                 "supplier": r["Preferred Supplier"]} for r in csv.DictReader(f)]
