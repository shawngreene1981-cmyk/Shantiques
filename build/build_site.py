"""Build the Shantiques window shop from the tracker.

Inputs
  data/inventory.json   Inventory!A2:X (header row + data rows) exactly as Sheets returns them
  data/photos/<ID>.jpg  original photos staged from the Shantiques Photos folder
  img_overrides/<ID>.jpg  optional cleaned-up photo used instead of the original (e.g. background removed)
  scenes.json           shop-the-wall photos; each spot names an Item ID
Output
  index.html + img/      upload the whole folder to Netlify
  Shantiques-WindowShop.html   single-file copy with images built in

Rules
  An item shows when "Show on Website" is checked and Status is not Removed.
  Sold items stay up, marked Sold, for SOLD_DAYS after Date Sold, then drop off.
  "New" = Date Listed within NEW_DAYS of the build date, or not listed yet.
"""
import base64, json, os, re, sys
from datetime import date, datetime
from PIL import Image, ImageOps

NEW_DAYS = 21
SOLD_DAYS = 14
HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(HERE, *a)
today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()


def money(v):
    v = (v or "").strip().replace("$", "").replace(",", "")
    if v in ("", "-", "PENDING", "unknown"):
        return None
    try:
        n = float(v.strip("()"))
    except ValueError:
        return None
    if n <= 0:
        return None
    return int(n) if n == int(n) else round(n, 2)


def day(v):
    v = (v or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            pass
    return None


rows = json.load(open(P("data", "inventory.json")))
head, data = rows[0], rows[1:]
col = {h: i for i, h in enumerate(head)}
need = ["Item ID", "Description", "Category", "List Price", "Date Listed", "Status", "Date Sold", "Show on Website"]
missing = [h for h in need if h not in col]
if missing:
    sys.exit(f"tracker columns missing: {missing}")


def get(r, h):
    i = col[h]
    return r[i] if i < len(r) else ""


os.makedirs(P("img"), exist_ok=True)


def photo(item_id):
    out = P("img", f"{item_id}.jpg")
    src = P("img_overrides", f"{item_id}.jpg")
    if not os.path.exists(src):
        src = P("data", "photos", f"{item_id}.jpg")
    if not os.path.exists(src):
        return None
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((900, 900))
    im.save(out, "JPEG", quality=82, optimize=True)
    return f"img/{item_id}.jpg"


all_items, shown, problems = {}, [], []
for n, r in enumerate(data):
    iid = get(r, "Item ID").strip()
    if not re.fullmatch(r"SH-\d{4}", iid):
        continue
    status = get(r, "Status").strip()
    listed, sold = day(get(r, "Date Listed")), day(get(r, "Date Sold"))
    it = {
        "id": iid,
        "description": get(r, "Description").strip(),
        "category": get(r, "Category").strip(),
        "listPrice": money(get(r, "List Price")),
        "status": status,
        "isNew": listed is None or (today - listed).days <= NEW_DAYS,
        "order": n,
    }
    all_items[iid] = it
    if get(r, "Show on Website").strip().upper() != "TRUE" or status == "Removed":
        continue
    if status == "Sold" and (sold is None or (today - sold).days > SOLD_DAYS):
        continue
    it["img"] = photo(iid)
    if not it["img"]:
        problems.append(f"{iid}: no photo in data/photos")
        continue
    shown.append(it)

scenes = json.load(open(P("scenes.json")))
for sc in scenes:
    for sp in sc["spots"]:
        it = all_items.get(sp.get("id", ""))
        if not it:
            problems.append(f"scene spot {sp['n']}: {sp.get('id')} not in tracker")
            continue
        sp["name"], sp["category"] = it["description"], it["category"]
        sp["price"] = None if it["status"] == "Sold" else it["listPrice"]
        if it["status"] == "Removed":
            sp["gone"] = True
        img = it.get("img") or photo(it["id"])
        if img:
            sp["item"] = dict(it, img=img)

shop = {"mall": "", "city": "", "booth": "", "updated": today.strftime("%b %-d, %Y")}
stats = {"total": 0, "byCat": {}}
for it in all_items.values():
    if it["status"] in ("Sold", "Removed"):
        continue
    stats["total"] += 1
    if it["category"]:
        stats["byCat"][it["category"]] = stats["byCat"].get(it["category"], 0) + 1
cfg = json.load(open(P("site_config.json"))) if os.path.exists(P("site_config.json")) else {}
token = (cfg.get("cloudflare_analytics_token") or "").strip()
analytics = ("<script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
             "data-cf-beacon='{\"token\": \"%s\"}'></script>" % token) if token else ""
html = open(P("template.html")).read()
html = (html.replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False))
            .replace("/*SHOP*/null", json.dumps(shop))
            .replace('/*STATS*/{"total":0,"byCat":{}}', json.dumps(stats))
            .replace("<!--ANALYTICS-->", analytics)
            .replace("/*ITEMS*/[]", json.dumps(shown, ensure_ascii=False)))
open(P("index.html"), "w").write(html)

# single-file copy: every img/ reference inlined
def inline(m):
    path = P(m.group(1))
    mt = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[path.rsplit(".", 1)[1]]
    return '"data:%s;base64,%s"' % (mt, base64.b64encode(open(path, "rb").read()).decode())
single = re.sub(r'"(img/[^"]+)"', inline, html)
open(P("Shantiques-WindowShop.html"), "w").write(single)

print(f"built: {len(shown)} items on the site, {sum(len(s['spots']) for s in scenes)} scene spots")
for p in problems:
    print("CHECK:", p)
