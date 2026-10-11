"""Packages power-apps/canvas-app/PantrySupplyOrdering.msapp as a solution canvas app component."""
import datetime
import json
import os
import struct
import zlib
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MSAPP = os.path.join(ROOT, "power-apps", "canvas-app", "PantrySupplyOrdering.msapp")
APP_NAME = "cr_pantrysupplyordering_7a1c3"
DISPLAY_NAME = "Pantry Supply Ordering"
CLIENT_VERSION = "3.26021.0"
# Data sources as Studio names them in the maker's environment. Not shipped in the app: an app
# packed with these tables (and Studio's cached table metadata) failed to open in Studio, so the
# tables are added in Studio after import instead. Kept for reference.
PANTRY_TABLES = {
    "Pantry Items": ("cr_pantryitems", "cr_pantryitem"),
    "Suppliers": ("cr_suppliers", "cr_supplier"),
    "Order Line Items_1": ("cr_orderlineitems", "cr_orderlineitem"),
    "Approval History Records": ("cr_approvalhistories", "cr_approvalhistory"),
    "Supply Orders": ("cr_supplyorders", "cr_supplyorder"),
}



def icon_png(size=64, rgb=(0, 120, 212)):
    row = b"\x00" + bytes(rgb) * size
    chunk = lambda kind, data: (struct.pack(">I", len(data)) + kind + data
                                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * size))
            + chunk(b"IEND", b""))


def build(apps=None):
    """Returns (CanvasApps xml, root components xml, {zip path: content}).

    apps: list of (schema name, display name, msapp path, {data source name: (entity set, logical name)}).
    The Pantry app declares no tables: Studio fails to open apps packed with Dataverse tables, so
    the five tables are added in Studio (Data → Add data) after import.
    """
    apps = apps or [(APP_NAME, DISPLAY_NAME, MSAPP, {})]
    xml, roots, files = "  <CanvasApps>\n", "", {}
    for app in apps:
        app_xml, root, app_files = _app(*app)
        xml += app_xml
        roots += root
        files.update(app_files)
    return xml + "  </CanvasApps>\n", roots, files


def _app(app_name, display_name, msapp_path, tables):
    with open(msapp_path, "rb") as f:
        msapp = f.read()
    document = f"CanvasApps/{app_name}_DocumentUri.msapp"
    background = f"CanvasApps/{app_name}_BackgroundImageUri"
    database_refs = json.dumps({"default.cds": {
        "state": "Configured", "instanceUrl": "", "webApiVersion": "v9.0", "environmentVariableName": "",
        "dataSources": {name: {"entitySetName": es, "logicalName": ln} for name, (es, ln) in tables.items()},
    }} if tables else {})
    tags = json.dumps({
        "primaryDeviceWidth": "1366", "primaryDeviceHeight": "768", "supportsPortrait": "false",
        "supportsLandscape": "true", "primaryFormFactor": "Tablet", "showStatusBar": "false",
        "publisherVersion": CLIENT_VERSION, "minimumRequiredApiVersion": "2.2.0",
        "hasComponent": "false", "hasUnlockedComponent": "false", "isUnifiedRootApp": "false",
    })
    cds_deps = json.dumps({"cdsdependencies": [
        {"logicalname": ln, "componenttype": "entity"} for _, ln in tables.values()]})
    xml = f"""    <CanvasApp>
      <Name>{app_name}</Name>
      <AppVersion>{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}</AppVersion>
      <Status>Ready</Status>
      <CreatedByClientVersion>{CLIENT_VERSION}</CreatedByClientVersion>
      <MinClientVersion>{CLIENT_VERSION}</MinClientVersion>
      <Tags>{escape(tags)}</Tags>
      <IsCdsUpgraded>0</IsCdsUpgraded>
      <GalleryItemId xsi:nil="true"></GalleryItemId>
      <BackgroundColor>RGBA(0,120,212,1)</BackgroundColor>
      <DisplayName>{display_name}</DisplayName>
      <Description>Request, approve and track office pantry supply orders.</Description>
      <CommitMessage xsi:nil="true"></CommitMessage>
      <Publisher xsi:nil="true"></Publisher>
      <AuthorizationReferences>[]</AuthorizationReferences>
      <ConnectionReferences>{{}}</ConnectionReferences>
      <DatabaseReferences>{escape(database_refs)}</DatabaseReferences>
      <AppComponents>[]</AppComponents>
      <AppComponentDependencies>[]</AppComponentDependencies>
      <CanConsumeAppPass>1</CanConsumeAppPass>
      <CanvasAppType>0</CanvasAppType>
      <BypassConsent>0</BypassConsent>
      <AdminControlBypassConsent>0</AdminControlBypassConsent>
      <EmbeddedApp xsi:nil="true"></EmbeddedApp>
      <IntroducedVersion>1.0</IntroducedVersion>
      <CdsDependencies>{escape(cds_deps)}</CdsDependencies>
      <IsCustomizable>1</IsCustomizable>
      <BackgroundImageUri>/{background}</BackgroundImageUri>
      <DocumentUri>/{document}</DocumentUri>
    </CanvasApp>
"""
    root = f'      <RootComponent type="300" schemaName="{app_name}" behavior="0" />\n'
    return xml, root, {document: msapp, background: icon_png()}
