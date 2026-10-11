"""Generates the canvas app screens (Src/*.pa.yaml) from a small Fluent 2 design system.

Run: python3 power-apps/canvas-app/generate_screens.py, then validate_app.py to check properties and layout.
Control versions match what Power Apps Studio uses for this app (2026 modern controls).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Src")

TEXT, BUTTON, BADGE, SPINNER = "ModernText@1.0.0", "ModernButton@1.0.0", "ModernBadge@1.0.0", "ModernSpinner@1.1.0"
INPUT, NUMBER, COMBO = "ModernTextInput@1.1.2", "ModernNumberInput@1.1.2", "ModernCombobox@1.1.2"
DATE, TABS, ICON, AVATAR = "ModernDatePicker@1.0.2", "ModernTabList@1.0.2", "ModernIcon@1.1.1", "ModernAvatar@1.1.0"
CONTAINER, GALLERY, RECT, IMAGE = "GroupContainer@1.5.0", "Gallery@2.15.0", "Rectangle@2.3.0", "Image@2.2.3"
GALLERY_VARIANT = "BrowseLayout_Vertical_OneTextVariant_ver5.0"

OS, AS, AA = "[@'Order Status']", "[@'Approval Status']", "[@'Approval Action']"
OPEN_STATUSES = ["Draft", "Submitted", "Approved", "Ordered", "'Partially Received'"]
DONE_STATUSES = ["Received", "Rejected", "Cancelled"]
MONEY = '"#,##0.00"'
ROLES = ["Requester", "Approver", "Pantry Admin"]


# --- YAML emitter -------------------------------------------------------------

def _formula(key, value, ind):
    value = str(value)
    if "\n" in value or ": " in value or " #" in value or value.endswith(":"):
        return [f"{ind}{key}: |-"] + [f"{ind}  {line}" for line in ("=" + value).split("\n")]
    return [f"{ind}{key}: ={value}"]


def _explicit_layout(c, parent):
    """Sets FillPortions on every auto-layout child so sizing never depends on Studio defaults:
    containers and galleries fill the free space, everything else keeps its Width/Height."""
    if parent and parent.get("variant") == "AutoLayout" and "FillPortions" not in c["props"]:
        flexible = c["type"] in (CONTAINER, GALLERY)
        c["props"]["FillPortions"] = 1 if flexible else 0
        if flexible:
            horizontal = parent["props"].get("LayoutDirection") == "LayoutDirection.Horizontal"
            c["props"].setdefault("LayoutMinWidth" if horizontal else "LayoutMinHeight", 0)
    if parent and parent.get("variant") == "AutoLayout":
        # A child without a cross-axis size fills the container's cross axis.
        cross = "Height" if parent["props"].get("LayoutDirection") == "LayoutDirection.Horizontal" else "Width"
        stretched = parent["props"].get("LayoutAlignItems") == "LayoutAlignItems.Stretch"
        if cross not in c["props"] and not stretched:
            c["props"].setdefault("AlignInContainer", "AlignInContainer.Stretch")


def _control(c, ind, parent=None):
    _explicit_layout(c, parent)
    out = [f"{ind}- {c['name']}:", f"{ind}    Control: {c['type']}"]
    if c.get("variant"):
        out.append(f"{ind}    Variant: {c['variant']}")
    if c["props"]:
        out.append(f"{ind}    Properties:")
        for k in sorted(c["props"]):
            out += _formula(k, c["props"][k], ind + "      ")
    if c.get("children"):
        out.append(f"{ind}    Children:")
        for child in c["children"]:
            out += _control(child, ind + "      ", c)
    return out


def screen_yaml(name, props, children):
    out = ["Screens:", f"  {name}:", "    Properties:"]
    for k in sorted(props):
        out += _formula(k, props[k], "      ")
    out.append("    Children:")
    for child in children:
        out += _control(child, "      ")
    return "\n".join(out) + "\n"


def ctl(name, type_, variant=None, children=None, **props):
    return {"name": name, "type": type_, "variant": variant, "props": props, "children": children or []}


# --- Design system components ---------------------------------------------------

def text(name, value, size=14, weight="Normal", color="clrTextPrimary", **p):
    p.setdefault("Height", max(20, int(size * 1.6)))
    return ctl(name, TEXT, Text=value, Size=size, FontWeight=f"FontWeight.{weight}", Color=color, **p)


def button(name, label, on_select, appearance="Primary", icon=None, **p):
    if icon:
        p.setdefault("Icon", f'"{icon}"')
    p.setdefault("Height", 36)
    return ctl(name, BUTTON, Text=label, OnSelect=on_select, Appearance=f"ButtonAppearance.{appearance}", **p)


def badge(name, content, intent, **p):
    p.setdefault("Height", 24)
    return ctl(name, BADGE, Content=content, Intent=intent, Shape="BadgeShape.Rounded", **p)


def icon(name, glyph, color="clrTextSecondary", **p):
    p.setdefault("Width", 20)
    p.setdefault("Height", 20)
    return ctl(name, ICON, Icon=f'"{glyph}"', IconColor=color, **p)


def radius(r):
    return {k: r for k in ("RadiusTopLeft", "RadiusTopRight", "RadiusBottomLeft", "RadiusBottomRight")}


def box(name, direction, children, gap=8, pad=0, **p):
    props = dict(LayoutDirection=f"LayoutDirection.{direction}", LayoutGap=gap, DropShadow="DropShadow.None",
                 Fill="Color.Transparent")
    if pad:
        props.update(PaddingTop=pad, PaddingBottom=pad, PaddingLeft=pad, PaddingRight=pad)
    if direction == "Vertical":
        props["LayoutAlignItems"] = "LayoutAlignItems.Stretch"
    props.update(p)
    return ctl(name, CONTAINER, "AutoLayout", children, **props)


def card(name, direction, children, gap=12, pad=16, **p):
    p.setdefault("Fill", "clrSurface")
    p.setdefault("BorderColor", "clrStroke")
    p.setdefault("BorderThickness", 1)
    for k, v in radius(12).items():
        p.setdefault(k, v)
    return box(name, direction, children, gap=gap, pad=pad, **p)


def spacer(name):
    return box(name, "Horizontal", [], LayoutMinWidth=0, LayoutMinHeight=0)


def chip(name, glyph, accent, size=36):
    """Icon on a softly tinted rounded tile."""
    return ctl(name, CONTAINER, "ManualLayout", [
        icon(f"{name}Icon", glyph, accent, IconStyle="IconStyle.Filled", Width=20, Height=20,
             X=(size - 20) // 2, Y=(size - 20) // 2),
    ], Fill=f"ColorFade({accent}, 0.86)", Width=size, Height=size, FillPortions=0, **radius(10))


def gallery(name, items, template_size, children, **p):
    p.setdefault("LayoutMinHeight", 100)
    return ctl(name, GALLERY, GALLERY_VARIANT, children, Items=items, TemplateSize=template_size,
               Fill="Color.Transparent", **p)


def row_divider(name):
    return ctl(name, RECT, Fill="clrStroke", Height=1, Width="Parent.TemplateWidth", Y="Parent.TemplateHeight - 1")


def empty_state(name, glyph, message, visible):
    return box(name, "Vertical", [
        icon(f"{name}Icon", glyph, "clrTextTertiary", Width=28, Height=28),
        text(f"{name}Text", f'"{message}"', 13, color="clrTextSecondary", Align="Align.Center", Height=40),
    ], gap=6, Height=80, FillPortions=0, Visible=visible, LayoutJustifyContent="LayoutJustifyContent.Center")


def section_head(prefix, title, glyph, extra=()):
    return box(f"{prefix}Head", "Horizontal", [
        icon(f"{prefix}HeadIcon", glyph, "clrBrand", IconStyle="IconStyle.Filled"),
        text(f"{prefix}HeadTitle", f'"{title}"', 16, "Semibold", Height=28, FillPortions=1, LayoutMinWidth=0),
        *extra,
    ], gap=8, Height=36, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center")


def field(name, caption, value):
    return box(name, "Vertical", [
        text(f"{name}Caption", f'"{caption}"', 12, color="clrTextSecondary", Height=18),
        text(f"{name}Value", value, 14, "Semibold", Height=22),
    ], gap=2, LayoutMinWidth=110)


# --- Shared formulas ----------------------------------------------------------------

def status_intent(expr):
    return (f'Switch(Text({expr}), "Received", BadgeIntent.Positive, "Ordered", BadgeIntent.Positive, '
            f'"Approved", BadgeIntent.Highlight, "Submitted", BadgeIntent.Informative, '
            f'"Partially Received", BadgeIntent.Caution, "Rejected", BadgeIntent.Critical, BadgeIntent.Neutral)')


def status_badge(name, expr, **p):
    p.setdefault("Width", 128)
    return badge(name, f"Text({expr})", status_intent(expr), **p)


def stock_label(item):
    return (f'If({item}.\'Current Stock\' <= 0, "Out of stock", '
            f'{item}.\'Current Stock\' <= {item}.\'Minimum Stock Level\', "Low stock", "In stock")')


def stock_intent(item):
    return (f"If({item}.'Current Stock' <= 0, BadgeIntent.Critical, "
            f"{item}.'Current Stock' <= {item}.'Minimum Stock Level', BadgeIntent.Caution, BadgeIntent.Positive)")


def add_to_cart(item, qty):
    return f"""With({{existing: LookUp(colCart, Item.'Pantry Item' = {item}.'Pantry Item'), qty: {qty}}},
    If(IsBlank(existing),
        Collect(colCart, {{Item: {item}, Qty: qty}}),
        Patch(colCart, existing, {{Qty: existing.Qty + qty}})
    )
);
If({item}.'Current Stock' > {item}.'Minimum Stock Level',
    Notify({item}.'Item Name' & " added. Note: the pantry still has " & {item}.'Current Stock' & " in stock.", NotificationType.Warning),
    Notify({item}.'Item Name' & " added to your request.", NotificationType.Success)
)"""


def status_filter(statuses):
    return "(" + " || ".join(f"'Order Status' = {OS}.{s}" for s in statuses) + ")"


MY_ORDERS = "'Requested By' = gUserEmail"
LOW = "Filter(colItems, 'Current Stock' <= 'Minimum Stock Level')"


def busy(action):
    """Runs `action` with the busy overlay shown and errors reported."""
    return f"""UpdateContext({{locBusy: true}});
IfError(
    {action},
    Notify("Something went wrong: " & FirstError.Message, NotificationType.Error)
);
UpdateContext({{locBusy: false}})"""


# --- Page frame: navigation rail + header ------------------------------------------------

# key, label, icon, screen, roles that see it
NAV = [
    ("Home", "Dashboard", "Home", "HomeScreen", ROLES),
    ("NewOrder", "New request", "Add", "NewOrderScreen", ROLES),
    ("MyOrders", "My requests", "DocumentBulletList", "MyOrdersScreen", ROLES),
    ("Inventory", "Inventory", "Box", "InventoryScreen", ROLES),
    ("Approvals", "Approvals", "TaskListSquareLtr", "ApprovalsScreen", ["Approver", "Pantry Admin"]),
    ("Receiving", "Receiving", "VehicleTruckProfile", "ReceivingScreen", ["Pantry Admin"]),
]


def role_visible(roles):
    if set(roles) == set(ROLES):
        return None
    return " || ".join(f'gRole = "{r}"' for r in roles)


def nav_rail(prefix, current):
    items = []
    for key, label, glyph, screen, roles in NAV:
        selected = key == current
        caption = f'"{label}"'
        if key == "NewOrder":
            caption = f'"{label}" & If(CountRows(colCart) > 0, " (" & CountRows(colCart) & ")", "")'
        props = dict(IconStyle="IconStyle.Filled" if selected else "IconStyle.Outline",
                     Layout="If(App.Width < 900, ButtonLayout.IconOnly, ButtonLayout.IconBefore)",
                     Tooltip=f'"{label}"', AccessibleLabel=f'"{label}"', Height=40)
        if role_visible(roles):
            props["Visible"] = role_visible(roles)
        items.append(button(f"{prefix}Nav{key}", caption, f"Navigate({screen}, ScreenTransition.None)",
                            "Secondary" if selected else "Subtle", glyph, **props))
    # Leave screens the selected role can't use.
    allowed = next(r for k, _, _, _, r in NAV if k == current)
    leave = "" if set(allowed) == set(ROLES) else (
        f"; If(!({role_visible(allowed)}), Navigate(HomeScreen, ScreenTransition.None))")
    return box(f"{prefix}NavRail", "Vertical", [
        box(f"{prefix}Brand", "Horizontal", [
            ctl(f"{prefix}BrandTile", CONTAINER, "ManualLayout", [
                icon(f"{prefix}BrandIcon", "FoodPizza", "Color.White", IconStyle="IconStyle.Filled",
                     Width=22, Height=22, X=9, Y=9),
            ], Fill="clrBrand", Width=40, Height=40, FillPortions=0, **radius(10)),
            box(f"{prefix}BrandText", "Vertical", [
                text(f"{prefix}BrandName", '"Office Pantry"', 15, "Semibold", Height=22),
                text(f"{prefix}BrandSub", '"Supply ordering"', 11, color="clrTextSecondary", Height=16),
            ], gap=0, Visible="App.Width >= 900", LayoutJustifyContent="LayoutJustifyContent.Center"),
        ], gap=10, Height=56, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        ctl(f"{prefix}NavGap", RECT, Fill="Color.Transparent", Height=8, FillPortions=0),
        *items,
        spacer(f"{prefix}NavSpacer"),
        box(f"{prefix}RoleBox", "Vertical", [
            text(f"{prefix}RoleCaption", '"Viewing as"', 11, "Semibold", color="clrTextSecondary", Height=16),
            ctl(f"{prefix}Role", COMBO, Items="[" + ", ".join(f'"{r}"' for r in ROLES) + "]",
                DefaultSelectedItems="[gRole]", ItemDisplayText="ThisItem.Value", SelectMultiple="false",
                IsSearchable="false", AccessibleLabel='"Switch role"', Height=36,
                OnChange=f"Set(gRole, Coalesce(Self.Selected.Value, gRole)){leave}"),
        ], gap=4, Height=72, FillPortions=0, Visible="App.Width >= 900", Fill="clrCanvas",
            PaddingTop=8, PaddingBottom=8, PaddingLeft=8, PaddingRight=8, **radius(10)),
        box(f"{prefix}UserRow", "Horizontal", [
            ctl(f"{prefix}UserAvatar", AVATAR, Tooltip="User().FullName", Width=32, Height=32),
            box(f"{prefix}UserText", "Vertical", [
                text(f"{prefix}UserName", "User().FullName", 13, "Semibold", Height=20),
                text(f"{prefix}UserRoleText", "gRole", 11, color="clrTextSecondary", Height=16),
            ], gap=0, Visible="App.Width >= 900", LayoutJustifyContent="LayoutJustifyContent.Center"),
        ], gap=10, Height=52, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
    ], gap=4, pad=12, Width="If(App.Width < 900, 72, 240)", FillPortions=0, Fill="clrSurface",
        LayoutAlignItems="LayoutAlignItems.Stretch")


def page(name, prefix, current, title, subtitle, actions, body, overlays=(), screen_props=None):
    header = box(f"{prefix}Header", "Horizontal", [
        box(f"{prefix}TitleBlock", "Vertical", [
            text(f"{prefix}Title", f'"{title}"', 26, "Semibold", Height=38),
            text(f"{prefix}Subtitle", subtitle, 14, color="clrTextSecondary", Height=22),
        ], gap=2, LayoutJustifyContent="LayoutJustifyContent.Center"),
        box(f"{prefix}Actions", "Horizontal", actions, gap=8, FillPortions=0, Width=sum(int(a["props"]["Width"]) for a in actions) + 8 * max(0, len(actions) - 1),
            LayoutJustifyContent="LayoutJustifyContent.End", LayoutAlignItems="LayoutAlignItems.Center"),
    ], Height=64, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center")
    main = box(f"{prefix}Main", "Vertical", [header, *body], gap=16, pad=24,
               LayoutAlignItems="LayoutAlignItems.Stretch")
    root = box(f"{prefix}Root", "Horizontal", [nav_rail(prefix, current), main], gap=0,
               Width="Parent.Width", Height="Parent.Height", Fill="clrCanvas",
               LayoutAlignItems="LayoutAlignItems.Stretch")
    overlay = ctl(f"{prefix}Busy", CONTAINER, "ManualLayout", [
        ctl(f"{prefix}BusyCard", CONTAINER, "ManualLayout", [
            ctl(f"{prefix}BusySpinner", SPINNER, Label='"Working on it..."', Width=240, Height=80,
                X=20, Y=20, LabelPosition="SpinnerLabelPosition.Below"),
        ], Fill="clrSurface", Width=280, Height=120, X="(Parent.Width - Self.Width) / 2",
            Y="(Parent.Height - Self.Height) / 2", **radius(12)),
    ], Fill="RGBA(0, 0, 0, 0.35)", Width="Parent.Width", Height="Parent.Height", Visible="locBusy")
    props = {"Fill": "clrCanvas"}
    props.update(screen_props or {})
    return screen_yaml(name, props, [root, *overlays, overlay])


def confirm_dialog(prefix, visible, title, message, keep_label, confirm_label, on_confirm, on_cancel):
    return ctl(f"{prefix}Dialog", CONTAINER, "ManualLayout", [
        card(f"{prefix}DialogCard", "Vertical", [
            text(f"{prefix}DialogTitle", f'"{title}"', 20, "Semibold", Height=32),
            text(f"{prefix}DialogText", f'"{message}"', 14, color="clrTextSecondary", Height=60,
                 VerticalAlign="VerticalAlign.Top"),
            box(f"{prefix}DialogButtons", "Horizontal", [
                spacer(f"{prefix}DialogSpacer"),
                button(f"{prefix}DialogCancel", f'"{keep_label}"', on_cancel, "Secondary", Width=140),
                button(f"{prefix}DialogConfirm", f'"{confirm_label}"', on_confirm, "Primary", Width=160),
            ], Height=40, FillPortions=0),
        ], gap=16, pad=24, Width=440, Height=220, X="(Parent.Width - Self.Width) / 2",
            Y="(Parent.Height - Self.Height) / 2"),
    ], Fill="RGBA(0, 0, 0, 0.35)", Width="Parent.Width", Height="Parent.Height", Visible=visible)


def order_row(prefix, selected_expr, subtitle):
    """Gallery template for a supply order: number, subtitle, status badge, selection marker."""
    return [
        ctl(f"{prefix}SelBar", RECT, Fill="clrBrand", Width=3, Height="Parent.TemplateHeight - 20", Y=10,
            Visible=selected_expr),
        text(f"{prefix}Number", "ThisItem.'Order Number'", 14, "Semibold", X=14, Y=12, Width="Parent.TemplateWidth - 170"),
        text(f"{prefix}Meta", subtitle, 12, color="clrTextSecondary", X=14, Y=38, Width="Parent.TemplateWidth - 170"),
        status_badge(f"{prefix}Badge", "ThisItem.'Order Status'", X="Parent.TemplateWidth - 142", Y=24),
        row_divider(f"{prefix}Divider"),
    ]


def lines_gallery(prefix, order):
    return gallery(f"{prefix}Lines", f"Filter('Order Line Items', ThisRecord.'Supply Order'.'Supply Order' = {order}.'Supply Order')", 56, [
        text(f"{prefix}LnName", "ThisItem.'Line Item Name'", 13, "Semibold", X=4, Y=6, Width="Parent.TemplateWidth - 130"),
        text(f"{prefix}LnSupplier", 'Coalesce(ThisItem.Supplier.\'Supplier Name\', "No supplier set")', 12,
             color="clrTextSecondary", X=4, Y=30, Width="Parent.TemplateWidth - 130"),
        text(f"{prefix}LnQty", '"× " & ThisItem.Quantity', 14, "Semibold", Align="Align.Right",
             X="Parent.TemplateWidth - 120", Y=6, Width=112),
        text(f"{prefix}LnCost", f"Text(Coalesce(ThisItem.'Total Cost', 0), {MONEY})", 12, color="clrTextSecondary",
             Align="Align.Right", X="Parent.TemplateWidth - 120", Y=30, Width=112),
        row_divider(f"{prefix}LnDivider"),
    ])


# --- Screens ----------------------------------------------------------------------

def kpi(prefix, key, caption, value, hint, glyph, accent="clrBrand"):
    return card(f"{prefix}Kpi{key}", "Horizontal", [
        chip(f"{prefix}Kpi{key}Chip", glyph, accent, 40),
        box(f"{prefix}Kpi{key}Text", "Vertical", [
            text(f"{prefix}Kpi{key}Caption", f'"{caption}"', 13, "Semibold", color="clrTextSecondary", Height=20),
            text(f"{prefix}Kpi{key}Value", value, 28, "Semibold", Height=40),
            text(f"{prefix}Kpi{key}Hint", hint, 12, color="clrTextSecondary", Height=18),
        ], gap=0, LayoutJustifyContent="LayoutJustifyContent.Center"),
    ], gap=12, pad=14, LayoutMinWidth=200, LayoutAlignItems="LayoutAlignItems.Center")


def home_screen():
    p = "Hm"
    on_visible = f"""Concurrent(
    UpdateContext({{locMyOpen: CountRows(Filter('Supply Orders', {MY_ORDERS} && {status_filter(["Submitted", "Approved", "Ordered"])}))}}),
    UpdateContext({{locAwaiting: CountRows(Filter('Supply Orders', {MY_ORDERS} && 'Order Status' = {OS}.Submitted))}}),
    UpdateContext({{locPendingAll: CountRows(Filter('Supply Orders', 'Order Status' = {OS}.Submitted))}}),
    UpdateContext({{locToReceive: CountRows(Filter('Supply Orders', 'Order Status' = {OS}.Ordered || 'Order Status' = {OS}.Approved))}}),
    UpdateContext({{locRecent: FirstN(Sort(Filter('Supply Orders', {MY_ORDERS}), 'Created On', SortOrder.Descending), 6)}})
)"""
    hero_subtitle = f'''Switch(gRole,
    "Approver", locPendingAll & " request(s) are waiting for your decision.",
    "Pantry Admin", CountRows({LOW}) & " item(s) need restocking and " & locToReceive & " order(s) are on their way.",
    "Request pantry supplies and follow them from approval to delivery.")'''
    hero_action = '''Switch(gRole,
    "Approver", Navigate(ApprovalsScreen, ScreenTransition.None),
    "Pantry Admin", Navigate(ReceivingScreen, ScreenTransition.None),
    Navigate(NewOrderScreen, ScreenTransition.None))'''
    hero = ctl(f"{p}Hero", CONTAINER, "ManualLayout", [
        ctl(f"{p}HeroImage", IMAGE, Image="imgHero", ImagePosition="ImagePosition.Fill",
            Width="Parent.Width", Height="Parent.Height", **radius(12)),
        text(f"{p}HeroTitle", '"Good " & Switch(true, Hour(Now()) < 12, "morning", Hour(Now()) < 17, "afternoon", "evening") & ", " & First(Split(User().FullName, " ")).Value',
             24, "Semibold", "Color.White", X=28, Y=26, Width="Parent.Width - 280", Height=36),
        text(f"{p}HeroSubtitle", hero_subtitle, 14, color="RGBA(255, 255, 255, 0.88)",
             X=28, Y=66, Width="Parent.Width - 280", Height=40, VerticalAlign="VerticalAlign.Top"),
        button(f"{p}HeroAction", 'Switch(gRole, "Approver", "Review approvals", "Pantry Admin", "Receive orders", "New request")',
               hero_action, "Secondary", Icon='Switch(gRole, "Approver", "TaskListSquareLtr", "Pantry Admin", "VehicleTruckProfile", "Add")',
               X="Parent.Width - 216", Y=46, Width=188, Height=40),
    ], Height=132, FillPortions=0, **radius(12))

    kpis = box(f"{p}Kpis", "Horizontal", [
        kpi(p, "Low", "Low stock items", f"CountRows({LOW})", '"At or below minimum"', "Warning",
            f"If(CountRows({LOW}) > 0, clrDanger, clrSuccess)"),
        kpi(p, "Open", "My open requests", "locMyOpen", '"Waiting or in progress"', "DocumentBulletList"),
        kpi(p, "Awaiting", 'Approvals pending', 'If(gRole = "Requester", locAwaiting, locPendingAll)',
            'If(gRole = "Requester", "Waiting for a decision", "Across the office")', "Clock", "clrWarning"),
        kpi(p, "Catalog", "Items in catalog", "CountRows(colItems)", '"Ready to request"', "Box", "clrSuccess"),
    ], gap=16, Height=112, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Stretch")

    restock = card(f"{p}Restock", "Vertical", [
        section_head(f"{p}Rs", "Needs restocking", "Warning", [
            button(f"{p}RestockAll", '"View inventory"', "Navigate(InventoryScreen, ScreenTransition.None)", "Subtle",
                   "ArrowRight", Layout="ButtonLayout.IconAfter", Width=172)]),
        gallery(f"{p}RestockList", f"Sort({LOW}, 'Current Stock')", 64, [
            text(f"{p}RsName", "ThisItem.'Item Name'", 14, "Semibold", X=4, Y=10, Width="Parent.TemplateWidth - 260"),
            text(f"{p}RsMeta", '"In stock " & Coalesce(ThisItem.\'Current Stock\', 0) & "  ·  Minimum " & Coalesce(ThisItem.\'Minimum Stock Level\', 0)',
                 12, color="clrTextSecondary", X=4, Y=36, Width="Parent.TemplateWidth - 260"),
            badge(f"{p}RsBadge", stock_label("ThisItem"), stock_intent("ThisItem"),
                  X="Parent.TemplateWidth - 244", Y=20, Width=104),
            button(f"{p}RsAdd", '"Request"', add_to_cart("ThisItem", "Coalesce(ThisItem.'Reorder Quantity', 1)"),
                   "Outline", "Add", X="Parent.TemplateWidth - 128", Y=14, Width=120, Height=34,
                   Tooltip='"Add the reorder quantity to your request"'),
            row_divider(f"{p}RsDivider"),
        ]),
        empty_state(f"{p}RestockEmpty", "CheckmarkCircle", "Everything is well stocked.", f"IsEmpty({p}RestockList.AllItems)"),
    ], LayoutMinWidth=340, LayoutAlignItems="LayoutAlignItems.Stretch")

    recent = card(f"{p}Recent", "Vertical", [
        section_head(f"{p}Rc", "My recent requests", "History", [
            button(f"{p}RecentAll", '"All requests"', "Navigate(MyOrdersScreen, ScreenTransition.None)",
                   "Subtle", "ArrowRight", Layout="ButtonLayout.IconAfter", Width=156)]),
        gallery(f"{p}RecentList", "locRecent", 64, order_row(
            f"{p}Rc", "false",
            f'Text(ThisItem.\'Created On\', "dd mmm yyyy") & "  ·  " & Text(Coalesce(ThisItem.\'Total Amount\', 0), {MONEY})'),
            OnSelect="Set(gSelOrder, ThisItem); Navigate(MyOrdersScreen, ScreenTransition.None)"),
        empty_state(f"{p}RecentEmpty", "DocumentAdd", "You have no requests yet.", f"IsEmpty({p}RecentList.AllItems)"),
    ], LayoutMinWidth=340, LayoutAlignItems="LayoutAlignItems.Stretch")

    body = [hero, kpis, box(f"{p}Panels", "Horizontal", [restock, recent], gap=16,
                            LayoutAlignItems="LayoutAlignItems.Stretch")]
    actions = [button(f"{p}Refresh", '"Refresh"', "Refresh('Pantry Items'); ClearCollect(colItems, Sort('Pantry Items', 'Item Name'))",
                      "Subtle", "ArrowClockwise", Width=120)]
    return page("HomeScreen", p, "Home", "Dashboard", 'Text(Today(), "dddd, dd mmmm yyyy")',
                actions, body, screen_props={"OnVisible": on_visible})


def new_order_screen():
    p = "No"
    catalog_items = (f"Sort(Filter(colItems, (IsBlank({p}Search.Text) || StartsWith('Item Name', {p}Search.Text)) && "
                     f"(IsBlank({p}Category.Selected) || Category = {p}Category.Selected.Value)), 'Item Name')")
    total = "Sum(colCart, Qty * Coalesce(Item.'Unit Price', 0))"
    submit = f"""If(IsBlank({p}RequiredBy.SelectedDate),
    Notify("Choose a required-by date.", NotificationType.Error),
    UpdateContext({{locBusy: true}});
    IfError(
        Set(gNewOrder, Patch('Supply Orders', Defaults('Supply Orders'), {{
            'Order Number': "PO-" & Text(Now(), "yyyymmdd-hhmmss"),
            'Order Status': {OS}.Draft,
            'Required By Date': {p}RequiredBy.SelectedDate,
            Justification: {p}Justification.Text,
            'Delivery Address': {p}Location.Text,
            'Requested By': gUserEmail,
            'Total Amount': {total}
        }}));
        ForAll(colCart As L,
            With({{item: LookUp('Pantry Items', 'Pantry Item' = L.Item.'Pantry Item')}},
                Patch('Order Line Items', Defaults('Order Line Items'), {{
                    'Line Item Name': item.'Item Name',
                    'Supply Order': gNewOrder,
                    'Pantry Item': item,
                    Supplier: item.'Preferred Supplier',
                    Quantity: L.Qty,
                    'Unit Price': item.'Unit Price',
                    'Total Cost': L.Qty * Coalesce(item.'Unit Price', 0)
                }})
            )
        );
        Patch('Supply Orders', gNewOrder, {{'Order Status': {OS}.Submitted}});
        Notify("Request " & gNewOrder.'Order Number' & " submitted for approval.", NotificationType.Success);
        Clear(colCart);
        Reset({p}Justification);
        Reset({p}Location);
        Set(gSelOrder, gNewOrder);
        UpdateContext({{locBusy: false}});
        Navigate(MyOrdersScreen, ScreenTransition.None),
        UpdateContext({{locBusy: false}});
        Notify("Your request couldn't be submitted: " & FirstError.Message, NotificationType.Error)
    )
)"""
    catalog = card(f"{p}Catalog", "Vertical", [
        section_head(f"{p}Cat", "1. Choose items", "Box"),
        box(f"{p}Toolbar", "Horizontal", [
            ctl(f"{p}Search", INPUT, Placeholder='"Search items"', Type="TextInputType.Search",
                TriggerOutput="TriggerOutput.Delayed", AccessibleLabel='"Search items"', Height=36, FillPortions=1,
                LayoutMinWidth=120),
            ctl(f"{p}Category", COMBO, Items="Choices('Item Category')", ItemDisplayText="ThisItem.Value",
                SelectMultiple="false", InputTextPlaceholder='"All categories"', AccessibleLabel='"Filter by category"',
                Width=220, Height=36),
        ], Height=36, FillPortions=0),
        gallery(f"{p}Items", catalog_items, 76, [
            text(f"{p}ItName", "ThisItem.'Item Name'", 14, "Semibold", X=4, Y=12, Width="Parent.TemplateWidth - 390"),
            text(f"{p}ItMeta", f'Text(ThisItem.Category) & "  ·  " & Text(ThisItem.\'Unit of Measure\') & "  ·  " & Text(Coalesce(ThisItem.\'Unit Price\', 0), {MONEY})',
                 12, color="clrTextSecondary", X=4, Y=40, Width="Parent.TemplateWidth - 390"),
            badge(f"{p}ItStock", f"{stock_label('ThisItem')} & \" · \" & Coalesce(ThisItem.'Current Stock', 0)",
                  stock_intent("ThisItem"), X="Parent.TemplateWidth - 376", Y=26, Width=136),
            ctl(f"{p}ItQty", NUMBER, Default=1, Min=1, Max=999, Step=1, Precision="DecimalPrecision.'0'",
                AccessibleLabel='"Quantity of " & ThisItem.\'Item Name\'', X="Parent.TemplateWidth - 228", Y=20,
                Width=96, Height=36),
            button(f"{p}ItAdd", '"Add"', add_to_cart("ThisItem", f"{p}ItQty.Value"), "Outline", "Add",
                   X="Parent.TemplateWidth - 120", Y=20, Width=112),
            row_divider(f"{p}ItDivider"),
        ]),
        empty_state(f"{p}ItemsEmpty", "SearchInfo", "No items match your search.", f"IsEmpty({p}Items.AllItems)"),
    ], LayoutMinWidth=440, LayoutAlignItems="LayoutAlignItems.Stretch")

    label = lambda name, value: text(name, value, 13, "Semibold", Height=20)
    cart = card(f"{p}Cart", "Vertical", [
        section_head(f"{p}Ct", "2. Your request", "Cart", [
            badge(f"{p}CartCount", 'CountRows(colCart) & If(CountRows(colCart) = 1, " item", " items")',
                  "BadgeIntent.Informative", Width=80)]),
        empty_state(f"{p}CartEmpty", "Cart", "Add items from the catalog to start a request.", "IsEmpty(colCart)"),
        gallery(f"{p}CartList", "colCart", 60, [
            text(f"{p}CtName", "ThisItem.Item.'Item Name'", 13, "Semibold", X=4, Y=8, Width="Parent.TemplateWidth - 150"),
            text(f"{p}CtLine", f"Text(ThisItem.Qty * Coalesce(ThisItem.Item.'Unit Price', 0), {MONEY})", 12,
                 color="clrTextSecondary", X=4, Y=32, Width="Parent.TemplateWidth - 150"),
            ctl(f"{p}CtQty", NUMBER, Default="ThisItem.Qty", Min=1, Max=999, Step=1, Precision="DecimalPrecision.'0'",
                OnChange="Patch(colCart, ThisItem, {Qty: Self.Value})",
                AccessibleLabel='"Quantity of " & ThisItem.Item.\'Item Name\'',
                X="Parent.TemplateWidth - 140", Y=12, Width=88, Height=36),
            ctl(f"{p}CtRemove", ICON, Icon='"Delete"', IconColor="clrDanger", OnSelect="Remove(colCart, ThisItem)",
                Tooltip='"Remove"', AccessibleLabel='"Remove " & ThisItem.Item.\'Item Name\'',
                X="Parent.TemplateWidth - 40", Y=18, Width=24, Height=24),
            row_divider(f"{p}CtDivider"),
        ], LayoutMinHeight=120, Visible="!IsEmpty(colCart)"),
        box(f"{p}TotalRow", "Horizontal", [
            text(f"{p}TotalLabel", '"Estimated total"', 14, "Semibold", FillPortions=1),
            text(f"{p}TotalValue", f"Text({total}, {MONEY})", 18, "Semibold", "clrBrand", Align="Align.Right",
                 Width=150, FillPortions=0),
        ], Height=32, FillPortions=0, Fill="clrBrandTint", PaddingLeft=12, PaddingRight=12,
            LayoutAlignItems="LayoutAlignItems.Center", **radius(8)),
        label(f"{p}RequiredByLabel", '"Required by"'),
        ctl(f"{p}RequiredBy", DATE, DefaultDate="DateAdd(Today(), 3, TimeUnit.Days)", StartDate="Today()",
            AccessibleLabel='"Required by date"', Height=36),
        label(f"{p}LocationLabel", '"Delivery location"'),
        ctl(f"{p}Location", INPUT, Placeholder='"For example: 3rd floor pantry"', AccessibleLabel='"Delivery location"', Height=36),
        label(f"{p}JustificationLabel", '"Justification (optional)"'),
        ctl(f"{p}Justification", INPUT, Placeholder='"Why is this needed?"', Type="TextInputType.Multiline",
            TriggerOutput="TriggerOutput.FocusOut", MaxLength=1000, AccessibleLabel='"Justification"', Height=72),
        button(f"{p}Submit", '"Submit for approval"', submit, "Primary", "Send", Height=42,
               DisplayMode="If(IsEmpty(colCart) || locBusy, DisplayMode.Disabled, DisplayMode.Edit)"),
    ], gap=10, Width="If(App.Width < 1200, 350, 410)", FillPortions=0, LayoutAlignItems="LayoutAlignItems.Stretch",
        LayoutOverflowY="LayoutOverflow.Scroll")

    body = [box(f"{p}Body", "Horizontal", [catalog, cart], gap=16, LayoutAlignItems="LayoutAlignItems.Stretch")]
    actions = [button(f"{p}Clear", '"Clear request"', "Clear(colCart)", "Subtle", "Dismiss", Width=164,
                      DisplayMode="If(IsEmpty(colCart), DisplayMode.Disabled, DisplayMode.Edit)")]
    return page("NewOrderScreen", p, "NewOrder", "New request",
                '"Pick the supplies you need. Your approver is notified when you submit."', actions, body)


def my_orders_screen():
    p = "Mo"
    base = f"{MY_ORDERS} && StartsWith('Order Number', {p}Search.Text)"
    items = f"""Sort(
    Switch({p}Tabs.Selected.Value,
        "Open", Filter('Supply Orders', {base} && {status_filter(OPEN_STATUSES)}),
        "Completed", Filter('Supply Orders', {base} && {status_filter(DONE_STATUSES)}),
        Filter('Supply Orders', {base})
    ),
    'Created On', SortOrder.Descending
)"""
    o = "gSelOrder"
    selected = f"!IsBlank({o}) && ThisItem.'Supply Order' = {o}.'Supply Order'"
    order_list = card(f"{p}List", "Vertical", [
        ctl(f"{p}Tabs", TABS, Items='["All", "Open", "Completed"]', Appearance="TabListAppearance.SubtleCircular",
            Alignment="TabListAlignment.Start", AccessibleLabel='"Filter requests"', Height=40),
        ctl(f"{p}Search", INPUT, Placeholder='"Search by request number"', Type="TextInputType.Search",
            TriggerOutput="TriggerOutput.Delayed", AccessibleLabel='"Search requests"', Height=36),
        gallery(f"{p}Orders", items, 72, order_row(
            f"{p}Or", selected,
            f'Text(ThisItem.\'Created On\', "dd mmm yyyy") & "  ·  " & Text(Coalesce(ThisItem.\'Total Amount\', 0), {MONEY})'),
            OnSelect=f"Set({o}, ThisItem)", TemplateFill=f"If({selected}, clrBrandTint, Color.Transparent)"),
        empty_state(f"{p}OrdersEmpty", "DocumentSearch", "No requests found.", f"IsEmpty({p}Orders.AllItems)"),
    ], gap=10, Width="If(App.Width < 1200, 360, 420)", FillPortions=0, LayoutAlignItems="LayoutAlignItems.Stretch")

    history = f"Sort(Filter('Approval History Records', ThisRecord.'Supply Order'.'Supply Order' = {o}.'Supply Order'), 'Action Date', SortOrder.Descending)"
    detail_body = box(f"{p}DetailBody", "Vertical", [
        box(f"{p}DetailHead", "Horizontal", [
            text(f"{p}DetailNumber", f"{o}.'Order Number'", 20, "Semibold", Height=32, FillPortions=1),
            status_badge(f"{p}DetailBadge", f"{o}.'Order Status'", Width=140, Height=28),
            button(f"{p}CancelBtn", '"Cancel request"', "UpdateContext({locConfirmCancel: true})", "Outline", "Dismiss",
                   Width=176, Visible=f"Text({o}.'Order Status') in [\"Draft\", \"Submitted\"]"),
        ], gap=12, Height=40, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        box(f"{p}Fields", "Horizontal", [
            field(f"{p}FCreated", "Created", f'Text({o}.\'Created On\', "dd mmm yyyy")'),
            field(f"{p}FRequired", "Required by", f'Text({o}.\'Required By Date\', "dd mmm yyyy")'),
            field(f"{p}FTotal", "Estimated total", f"Text(Coalesce({o}.'Total Amount', 0), {MONEY})"),
            field(f"{p}FApproval", "Approval", f'Coalesce(Text({o}.\'Approval Status\'), "Not started")'),
        ], gap=16, Height=48, FillPortions=0),
        text(f"{p}Comments", f'"Approver comments: " & {o}.\'Approver Comments\'', 13, color="clrTextSecondary",
             Visible=f"!IsBlank({o}.'Approver Comments')", Height=40, VerticalAlign="VerticalAlign.Top"),
        box(f"{p}DetailCols", "Horizontal", [
            box(f"{p}LinesCol", "Vertical", [
                section_head(f"{p}Ln", "Items", "BoxMultiple"),
                lines_gallery(p, o),
            ], gap=8, LayoutAlignItems="LayoutAlignItems.Stretch"),
            box(f"{p}HistoryCol", "Vertical", [
                section_head(f"{p}Hs", "Approval history", "History"),
                gallery(f"{p}History", history, 64, [
                    icon(f"{p}HsDot", "CircleSmall", "clrBrand", IconStyle="IconStyle.Filled", Y=8),
                    text(f"{p}HsAction", 'Text(ThisItem.Action) & " by " & Coalesce(ThisItem.Approver, "system")', 13,
                         "Semibold", X=24, Y=6, Width="Parent.TemplateWidth - 28"),
                    text(f"{p}HsMeta", 'Text(ThisItem.\'Action Date\', "dd mmm yyyy, hh:mm") & If(IsBlank(ThisItem.Comments), "", "  ·  " & ThisItem.Comments)',
                         12, color="clrTextSecondary", X=24, Y=30, Width="Parent.TemplateWidth - 28"),
                ]),
                empty_state(f"{p}HistoryEmpty", "History", "No approval activity yet.", f"IsEmpty({p}History.AllItems)"),
            ], gap=8, LayoutAlignItems="LayoutAlignItems.Stretch"),
        ], gap=24, LayoutAlignItems="LayoutAlignItems.Stretch"),
    ], gap=16, Visible=f"!IsBlank({o})", LayoutAlignItems="LayoutAlignItems.Stretch",
        LayoutOverflowY="LayoutOverflow.Scroll")
    detail = card(f"{p}Detail", "Vertical", [
        detail_body,
        empty_state(f"{p}DetailEmpty", "DocumentBulletList", "Select a request to see its items and approval history.",
                    f"IsBlank({o})"),
    ], gap=16, pad=24, LayoutMinWidth=440, LayoutAlignItems="LayoutAlignItems.Stretch")

    cancel = f"""UpdateContext({{locConfirmCancel: false}});
{busy(f'''Patch('Supply Orders', {o}, {{'Order Status': {OS}.Cancelled}});
    Set({o}, LookUp('Supply Orders', 'Supply Order' = {o}.'Supply Order'));
    Notify("Request cancelled.", NotificationType.Success)''')}"""
    dialog = confirm_dialog(p, "locConfirmCancel", "Cancel this request?",
                            "The request will be marked as cancelled and won't be sent to suppliers.",
                            "Keep request", "Cancel request", cancel, "UpdateContext({locConfirmCancel: false})")
    body = [box(f"{p}Body", "Horizontal", [order_list, detail], gap=16, LayoutAlignItems="LayoutAlignItems.Stretch")]
    refresh = f"Refresh('Supply Orders'); If(!IsBlank({o}), Set({o}, LookUp('Supply Orders', 'Supply Order' = {o}.'Supply Order')))"
    actions = [
        button(f"{p}Refresh", '"Refresh"', refresh, "Subtle", "ArrowClockwise", Width=120),
        button(f"{p}New", '"New request"', "Navigate(NewOrderScreen, ScreenTransition.None)", "Primary", "Add", Width=150),
    ]
    on_visible = f"If(!IsBlank({o}), Set({o}, LookUp('Supply Orders', 'Supply Order' = {o}.'Supply Order')))"
    return page("MyOrdersScreen", p, "MyOrders", "My requests", '"Track your supply requests and their approvals."',
                actions, body, overlays=[dialog], screen_props={"OnVisible": on_visible})


def inventory_screen():
    p = "Iv"
    items = (f"Sort(Filter(colItems, (IsBlank({p}Search.Text) || StartsWith('Item Name', {p}Search.Text) || StartsWith(SKU, {p}Search.Text)) && "
             f"(IsBlank({p}Category.Selected) || Category = {p}Category.Selected.Value) && "
             f"Switch({p}Tabs.Selected.Value, \"Low stock\", 'Current Stock' <= 'Minimum Stock Level', "
             f"\"Out of stock\", 'Current Stock' <= 0, true)), 'Item Name')")
    admin = 'gRole = "Pantry Admin"'
    # (key, header, cell formula, x fraction, width fraction, align). Fractions are of the width left
    # after the fixed Status (110) and Request (112) columns, so the columns never collide.
    cols = [
        ("Item", "Item", "ThisItem.'Item Name'", 0.00, 0.30, "Left"),
        ("Cat", "Category", "Text(ThisItem.Category)", 0.30, 0.18, "Left"),
        ("Stock", "In stock", "Coalesce(ThisItem.'Current Stock', 0)", 0.48, 0.11, "Right"),
        ("Min", "Minimum", "Coalesce(ThisItem.'Minimum Stock Level', 0)", 0.59, 0.11, "Right"),
        ("Price", "Unit price", f"Text(Coalesce(ThisItem.'Unit Price', 0), {MONEY})", 0.70, 0.13, "Right"),
        ("Loc", "Location", "Coalesce(ThisItem.'Storage Location', \"-\")", 0.83, 0.17, "Left"),
    ]
    fixed = 256
    header_cells = [text(f"{p}H{k}", f'"{h}"', 12, "Semibold", color="clrTextSecondary", Align=f"Align.{a}",
                         X=f"(Parent.Width - {fixed}) * {x} + 12", Y=10, Width=f"(Parent.Width - {fixed}) * {w} - 8",
                         Height=20)
                    for k, h, _, x, w, a in cols]
    header_cells.append(text(f"{p}HStatus", '"Status"', 12, "Semibold", color="clrTextSecondary",
                             X="Parent.Width - 244", Y=10, Width=110, Height=20))
    row_cells = []
    for k, _, f, x, w, a in cols:
        cell = text(f"{p}C{k}", f, 13, "Semibold" if k == "Item" else "Normal", Align=f"Align.{a}",
                    X=f"(Parent.TemplateWidth - {fixed}) * {x} + 12", Y=16,
                    Width=f"(Parent.TemplateWidth - {fixed}) * {w} - 8", Height=24)
        if k == "Stock":
            cell["props"]["Visible"] = f"!({admin})"
        row_cells.append(cell)
    save_stock = f"""IfError(
    Patch('Pantry Items', ThisItem, {{'Current Stock': Self.Value}});
    Patch(colItems, ThisItem, {{'Current Stock': Self.Value}});
    Notify(ThisItem.'Item Name' & " stock set to " & Self.Value & ".", NotificationType.Success),
    Notify("Couldn't update stock: " & FirstError.Message, NotificationType.Error)
)"""
    row_cells += [
        ctl(f"{p}CStockEdit", NUMBER, Default="Coalesce(ThisItem.'Current Stock', 0)", Min=0, Max=99999, Step=1,
            Precision="DecimalPrecision.'0'", OnChange=save_stock, Visible=admin,
            AccessibleLabel='"Stock of " & ThisItem.\'Item Name\'',
            X=f"(Parent.TemplateWidth - {fixed}) * 0.48 + 4", Y=10, Width=f"(Parent.TemplateWidth - {fixed}) * 0.11",
            Height=36),
        badge(f"{p}CStatus", stock_label("ThisItem"), stock_intent("ThisItem"),
              X="Parent.TemplateWidth - 244", Y=16, Width=110),
        button(f"{p}CAdd", '"Request"', add_to_cart("ThisItem", "Coalesce(ThisItem.'Reorder Quantity', 1)"), "Subtle", "Add",
               X="Parent.TemplateWidth - 124", Y=10, Width=112, Height=36,
               Tooltip='"Add the reorder quantity to your request"'),
        row_divider(f"{p}CDivider"),
    ]
    toolbar = box(f"{p}Toolbar", "Horizontal", [
        ctl(f"{p}Tabs", TABS, Items='["All", "Low stock", "Out of stock"]', Appearance="TabListAppearance.SubtleCircular",
            Alignment="TabListAlignment.Start", AccessibleLabel='"Filter by stock level"', Width=360, Height=40),
        spacer(f"{p}ToolbarSpacer"),
        ctl(f"{p}Search", INPUT, Placeholder='"Search by name or SKU"', Type="TextInputType.Search",
            TriggerOutput="TriggerOutput.Delayed", AccessibleLabel='"Search inventory"', Width=280, Height=36),
        ctl(f"{p}Category", COMBO, Items="Choices('Item Category')", ItemDisplayText="ThisItem.Value",
            SelectMultiple="false", InputTextPlaceholder='"All categories"', AccessibleLabel='"Filter by category"',
            Width=220, Height=36),
    ], gap=12, Height=40, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center")
    table = card(f"{p}Table", "Vertical", [
        ctl(f"{p}HeaderRow", CONTAINER, "ManualLayout", header_cells, Height=40, FillPortions=0,
            Fill="clrCanvas", **radius(8)),
        gallery(f"{p}Rows", items, 56, row_cells),
        empty_state(f"{p}RowsEmpty", "SearchInfo", "No items match these filters.", f"IsEmpty({p}Rows.AllItems)"),
        text(f"{p}Count", f'CountRows({p}Rows.AllItems) & " of " & CountRows(colItems) & " items" & If({admin}, "  ·  Edit a stock number and click away to save it.", "")',
             12, color="clrTextSecondary", Height=18),
    ], gap=8, LayoutAlignItems="LayoutAlignItems.Stretch")
    actions = [button(f"{p}Refresh", '"Refresh"', "Refresh('Pantry Items'); ClearCollect(colItems, Sort('Pantry Items', 'Item Name'))",
                      "Subtle", "ArrowClockwise", Width=120)]
    return page("InventoryScreen", p, "Inventory", "Inventory",
                'If(gRole = "Pantry Admin", "Update stock counts and request anything that is running low.", "Current stock for every pantry item. Request anything that is running low.")',
                actions, [toolbar, table])


def decision_screen(p, screen, nav_key, title, subtitle, tabs, items_by_tab, sel, detail_extra, actions_row):
    """Shared master-detail layout for the Approvals and Receiving screens."""
    selected = f"!IsBlank({sel}) && ThisItem.'Supply Order' = {sel}.'Supply Order'"
    switch = ",\n        ".join(f'"{t}", {f}' for t, f in list(items_by_tab.items())[1:])
    first = list(items_by_tab.values())[0]
    items = f"Switch({p}Tabs.Selected.Value,\n        {switch},\n        {first})"
    order_list = card(f"{p}List", "Vertical", [
        ctl(f"{p}Tabs", TABS, Items="[" + ", ".join(f'"{t}"' for t in tabs) + "]",
            Appearance="TabListAppearance.SubtleCircular", Alignment="TabListAlignment.Start",
            AccessibleLabel=f'"Filter {title.lower()}"', Height=40),
        gallery(f"{p}Orders", items, 72, order_row(
            f"{p}Or", selected,
            f'ThisItem.\'Requested By\' & "  ·  " & Text(Coalesce(ThisItem.\'Total Amount\', 0), {MONEY})'),
            OnSelect=f"Set({sel}, ThisItem)", TemplateFill=f"If({selected}, clrBrandTint, Color.Transparent)"),
        empty_state(f"{p}OrdersEmpty", "CheckmarkCircle", "Nothing here right now.", f"IsEmpty({p}Orders.AllItems)"),
    ], gap=10, Width="If(App.Width < 1200, 380, 440)", FillPortions=0, LayoutAlignItems="LayoutAlignItems.Stretch")
    detail_body = box(f"{p}DetailBody", "Vertical", [
        box(f"{p}DetailHead", "Horizontal", [
            text(f"{p}DetailNumber", f"{sel}.'Order Number'", 20, "Semibold", Height=32, FillPortions=1),
            status_badge(f"{p}DetailBadge", f"{sel}.'Order Status'", Width=140, Height=28),
        ], gap=12, Height=40, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        box(f"{p}Fields", "Horizontal", [
            field(f"{p}FBy", "Requested by", f"{sel}.'Requested By'"),
            field(f"{p}FRequired", "Required by", f'Text({sel}.\'Required By Date\', "dd mmm yyyy")'),
            field(f"{p}FTotal", "Estimated total", f"Text(Coalesce({sel}.'Total Amount', 0), {MONEY})"),
            field(f"{p}FWhere", "Deliver to", f'Coalesce({sel}.\'Delivery Address\', "-")'),
        ], gap=16, Height=48, FillPortions=0),
        text(f"{p}Why", f'"Justification: " & Coalesce({sel}.Justification, "none given")', 13, color="clrTextSecondary",
             Height=40, VerticalAlign="VerticalAlign.Top"),
        section_head(f"{p}Ln", "Items", "BoxMultiple"),
        lines_gallery(p, sel),
        *detail_extra,
        actions_row,
    ], gap=12, Visible=f"!IsBlank({sel})", LayoutAlignItems="LayoutAlignItems.Stretch",
        LayoutOverflowY="LayoutOverflow.Scroll")
    detail = card(f"{p}Detail", "Vertical", [
        detail_body,
        empty_state(f"{p}DetailEmpty", "DocumentBulletList", "Select a request to review it.", f"IsBlank({sel})"),
    ], gap=16, pad=24, LayoutMinWidth=440, LayoutAlignItems="LayoutAlignItems.Stretch")
    body = [box(f"{p}Body", "Horizontal", [order_list, detail], gap=16, LayoutAlignItems="LayoutAlignItems.Stretch")]
    actions = [button(f"{p}Refresh", '"Refresh"', f"Refresh('Supply Orders'); Set({sel}, Blank())",
                      "Subtle", "ArrowClockwise", Width=120)]
    return page(screen, p, nav_key, title, subtitle, actions, body)


def approvals_screen():
    p, sel = "Ap", "gApprOrder"
    decided = f"'Approval Status' = {AS}.Approved || 'Approval Status' = {AS}.Rejected"

    def decide(outcome, order_status, action):
        return busy(f'''Patch('Supply Orders', {sel}, {{
        'Approval Status': {AS}.{outcome},
        'Order Status': {OS}.{order_status},
        'Approval Date': Now(),
        'Approved By': User().FullName,
        'Approver Comments': {p}Comment.Text
    }});
    Patch('Approval History Records', Defaults('Approval History Records'), {{
        'Approval Record': "{outcome} - " & {sel}.'Order Number',
        'Supply Order': {sel},
        Action: {AA}.{action},
        Approver: User().FullName,
        'Action Date': Now(),
        Comments: {p}Comment.Text,
        'Previous Status': {AS}.Pending,
        'New Status': {AS}.{outcome}
    }});
    Notify({sel}.'Order Number' & " {outcome.lower()}.", NotificationType.Success);
    Set({sel}, Blank());
    Reset({p}Comment)''')

    reject = f'If(IsBlank({p}Comment.Text), Notify("Add a comment explaining why you are rejecting it.", NotificationType.Error), {decide("Rejected", "Rejected", "Rejected")})'
    pending = f"Text({sel}.'Order Status') = \"Submitted\""
    comment = ctl(f"{p}Comment", INPUT, Placeholder='"Comment for the requester (required to reject)"',
                  Type="TextInputType.Multiline", TriggerOutput="TriggerOutput.Keypress", MaxLength=1000,
                  AccessibleLabel='"Approver comment"', Height=64, Visible=pending)
    actions_row = box(f"{p}Decide", "Horizontal", [
        spacer(f"{p}DecideSpacer"),
        button(f"{p}Reject", '"Reject"', reject, "Outline", "DismissCircle", Width=130),
        button(f"{p}Approve", '"Approve"', decide("Approved", "Approved", "Approved"), "Primary", "CheckmarkCircle",
               Width=150),
    ], Height=40, FillPortions=0, Visible=pending)
    return decision_screen(
        p, "ApprovalsScreen", "Approvals", "Approvals",
        '"Review supply requests from the whole office. Approved requests are emailed to suppliers automatically."',
        ["Pending", "Decided"],
        {"Pending": f"Sort(Filter('Supply Orders', 'Order Status' = {OS}.Submitted), 'Created On', SortOrder.Ascending)",
         "Decided": f"Sort(Filter('Supply Orders', {decided}), 'Modified On', SortOrder.Descending)"},
        sel, [comment], actions_row)


def receiving_screen():
    p, sel = "Rv", "gRecvOrder"
    receive = busy(f'''ForAll(Filter('Order Line Items', ThisRecord.'Supply Order'.'Supply Order' = {sel}.'Supply Order') As L,
        With({{item: LookUp('Pantry Items', 'Pantry Item' = L.'Pantry Item'.'Pantry Item')}},
            If(!IsBlank(item), Patch('Pantry Items', item, {{'Current Stock': Coalesce(item.'Current Stock', 0) + L.Quantity}}))
        )
    );
    Patch('Supply Orders', {sel}, {{'Order Status': {OS}.Received}});
    ClearCollect(colItems, Sort('Pantry Items', 'Item Name'));
    Notify({sel}.'Order Number' & " received. Stock levels updated.", NotificationType.Success);
    Set({sel}, Blank())''')
    open_order = f"Text({sel}.'Order Status') in [\"Approved\", \"Ordered\", \"Partially Received\"]"
    actions_row = box(f"{p}Decide", "Horizontal", [
        text(f"{p}Hint", '"Marking it received adds every item quantity to the pantry stock."', 12,
             color="clrTextSecondary", Height=36, VerticalAlign="VerticalAlign.Middle", FillPortions=1),
        button(f"{p}Receive", '"Mark as received"', receive, "Primary", "CheckmarkCircle", Width=190, FillPortions=0),
    ], Height=40, FillPortions=0, Visible=open_order)
    return decision_screen(
        p, "ReceivingScreen", "Receiving", "Receiving",
        '"Record deliveries from suppliers. Received quantities are added to stock."',
        ["To receive", "Received"],
        {"To receive": f"Sort(Filter('Supply Orders', 'Order Status' = {OS}.Ordered || 'Order Status' = {OS}.Approved || 'Order Status' = {OS}.'Partially Received'), 'Created On', SortOrder.Ascending)",
         "Received": f"Sort(Filter('Supply Orders', 'Order Status' = {OS}.Received), 'Modified On', SortOrder.Descending)"},
        sel, [], actions_row)


HERO_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='140' viewBox='0 0 1200 140' preserveAspectRatio='none'>"
            "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#0F6CBD'/>"
            "<stop offset='1' stop-color='#2886DE'/></linearGradient></defs><rect width='1200' height='140' fill='url(#g)'/>"
            "<circle cx='1110' cy='10' r='120' fill='#FFFFFF' fill-opacity='0.08'/>"
            "<circle cx='960' cy='150' r='80' fill='#FFFFFF' fill-opacity='0.06'/></svg>")

APP = f"""App:
  Properties:
    Formulas: |-
      =clrBrand = ColorValue("#0F6CBD");
      clrBrandTint = ColorValue("#EBF3FC");
      clrCanvas = ColorValue("#F5F5F5");
      clrSurface = Color.White;
      clrStroke = ColorValue("#E0E0E0");
      clrTextPrimary = ColorValue("#242424");
      clrTextSecondary = ColorValue("#616161");
      clrTextTertiary = ColorValue("#9E9E9E");
      clrSuccess = ColorValue("#107C10");
      clrWarning = ColorValue("#BC4B09");
      clrDanger = ColorValue("#C50F1F");
      gUserEmail = Lower(User().Email);
      imgHero = "data:image/svg+xml;utf8," & EncodeUrl("{HERO_SVG}");
    OnStart: |-
      =Set(gRole, "Requester");
      ClearCollect(colItems, Sort('Pantry Items', 'Item Name'))
    Theme: =PantryTheme
"""

SCREENS = ["HomeScreen", "NewOrderScreen", "MyOrdersScreen", "InventoryScreen", "ApprovalsScreen", "ReceivingScreen"]


def main():
    for f in os.listdir(SRC):
        if f.endswith(".pa.yaml"):
            os.remove(os.path.join(SRC, f))
    files = {
        "App.pa.yaml": APP,
        "_EditorState.pa.yaml": "EditorState:\n  ScreensOrder:\n" + "".join(f"    - {s}\n" for s in SCREENS),
        "HomeScreen.pa.yaml": home_screen(),
        "NewOrderScreen.pa.yaml": new_order_screen(),
        "MyOrdersScreen.pa.yaml": my_orders_screen(),
        "InventoryScreen.pa.yaml": inventory_screen(),
        "ApprovalsScreen.pa.yaml": approvals_screen(),
        "ReceivingScreen.pa.yaml": receiving_screen(),
    }
    for name, content in files.items():
        with open(os.path.join(SRC, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Wrote Src/{name}")


if __name__ == "__main__":
    main()
