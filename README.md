# Shantiques window shop

The public site at https://shopshantiques.com, run by Shantiques L.L.C. (Springfield, Missouri).

- `site/` is what Netlify publishes. Every push to `main` goes live automatically.
- `build/` holds the template and `build_site.py`, which builds `site/` from the
  Shantiques-Tracker-CURRENT Google Sheet (Inventory tab) and the Shantiques Photos folder.
- `data/inventory.json` is the tracker snapshot used for the last build (public columns only).

Only items with **Show on Website** checked in the tracker appear on the site.
