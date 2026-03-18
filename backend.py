"""
FoodFlex Backend - Kroger + Open Food Facts
============================================
Two data sources, completely free:

1. KROGER API  -> real-time prices at 2,800+ US stores
   Requires free key: https://developer.kroger.com/manage/apps/register
   Add to .env:  KROGER_CLIENT_ID=xxx  KROGER_CLIENT_SECRET=xxx

2. OPEN FOOD FACTS API -> nutrition grades, allergens, images for 3M+ products
   No key needed. No signup. Just works.

SETUP:
  pip install flask flask-cors requests python-dotenv
  python3 backend.py
"""

import os
import base64
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
CORS(app)

# Config
KROGER_BASE   = "https://api.kroger.com/v1"
OFF_BASE      = "https://world.openfoodfacts.org"
OFF_HEADERS   = {"User-Agent": "FoodFlex/1.0 (foodflex@example.com)"}
CLIENT_ID     = os.getenv("KROGER_CLIENT_ID", "YOUR_CLIENT_ID")
CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET", "YOUR_CLIENT_SECRET")

# Caches
_token_cache = {"access_token": None, "expires_at": None}
_off_cache   = {}


# --- Kroger Auth --------------------------------------------------------------
def get_access_token():
    now = datetime.utcnow()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now:
        return _token_cache["access_token"]
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    resp = requests.post(
        f"{KROGER_BASE}/connect/oauth2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Authorization": f"Basic {encoded}"},
        data="grant_type=client_credentials&scope=product.compact",
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"]   = now + timedelta(seconds=data["expires_in"] - 60)
    return data["access_token"]


def kroger_get(endpoint, params=None):
    token = get_access_token()
    resp = requests.get(
        f"{KROGER_BASE}{endpoint}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params=params or {},
    )
    resp.raise_for_status()
    return resp.json()


# --- Open Food Facts ----------------------------------------------------------
GRADE_LABELS = {"A": "Excellent", "B": "Good", "C": "Fair", "D": "Poor", "E": "Bad"}
NOVA_LABELS  = {1: "Unprocessed", 2: "Culinary", 3: "Processed", 4: "Ultra-processed"}

def get_nutrition_data(term):
    """Search Open Food Facts by ingredient name. Cached per term."""
    key = term.lower().strip()
    if key in _off_cache:
        return _off_cache[key]
    try:
        # Retry up to 2 times — OFF can be slow
        resp = None
        for attempt in range(2):
            try:
                resp = requests.get(
                    f"{OFF_BASE}/cgi/search.pl",
            params={
                "search_terms": term,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 10,
                "fields": "product_name,nutrition_grades,nutriscore_score,allergens,nova_group,image_front_small_url,brands",
                "countries_tags": "en:united-states",
            },
                    headers=OFF_HEADERS,
                    timeout=15,
                )
                break  # success, stop retrying
            except requests.exceptions.Timeout:
                if attempt == 1:
                    return _empty_nutrition()
        if not resp:
            return _empty_nutrition()
        resp.raise_for_status()
        products = resp.json().get("products", [])
        result = _empty_nutrition()
        for p in products:
            # nutrition_grades comes back lowercase ("a","b","c","d","e")
            grade = (p.get("nutrition_grades") or "").strip().upper()
            if grade in ["A", "B", "C", "D", "E"]:
                allergen_str = p.get("allergens", "")
                allergens = [a.replace("en:", "").strip()
                             for a in allergen_str.split(",") if a.strip()] if allergen_str else []
                nova = p.get("nova_group")
                result = {
                    "nutrition_grade":       grade,
                    "nutrition_grade_label": GRADE_LABELS.get(grade),
                    "nutriscore":            p.get("nutriscore_score"),
                    "allergens":             allergens,
                    "nova_group":            nova,
                    "nova_label":            NOVA_LABELS.get(nova),
                    "off_image":             p.get("image_front_small_url"),
                    "off_brand":             (p.get("brands") or "").split(",")[0].strip() or None,
                }
                break
        _off_cache[key] = result
        return result
    except Exception:
        return _empty_nutrition()


def get_nutrition_by_barcode(barcode):
    """Look up a product on Open Food Facts by UPC barcode."""
    try:
        resp = requests.get(
            f"{OFF_BASE}/api/v2/product/{barcode}.json",
            headers=OFF_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != 1:
            return None
        p = data.get("product", {})
        grade = (p.get("nutrition_grades") or "").strip().upper()
        nova  = p.get("nova_group")
        return {
            "name":                  p.get("product_name", ""),
            "brand":                 p.get("brands", ""),
            "nutrition_grade":       grade or None,
            "nutrition_grade_label": GRADE_LABELS.get(grade),
            "nutriscore":            p.get("nutriscore_score"),
            "allergens":             p.get("allergens_tags", []),
            "nova_group":            nova,
            "nova_label":            NOVA_LABELS.get(nova),
            "image":                 p.get("image_front_small_url"),
            "ingredients":           p.get("ingredients_text", ""),
            "calories_per_100g":     p.get("nutriments", {}).get("energy-kcal_100g"),
        }
    except Exception:
        return None


def _empty_nutrition():
    return {"nutrition_grade": None, "nutrition_grade_label": None,
            "nutriscore": None, "allergens": [], "nova_group": None,
            "nova_label": None, "off_image": None, "off_brand": None}


# --- Kroger Product Search ----------------------------------------------------
def _search_product(term, location_id):
    """Search Kroger for price, enrich with Open Food Facts nutrition data."""
    try:
        data     = kroger_get("/products", {"filter.term": term,
                                             "filter.locationId": location_id,
                                             "filter.limit": 5})
        products = data.get("data", [])
        if not products:
            nutrition = get_nutrition_data(term)
            return {"ingredient": term, "found": False, "price": None,
                    "name": None, "upc": None, **nutrition}

        best = None
        best_price = float("inf")
        for p in products:
            for item in p.get("items", []):
                price_info = item.get("price", {})
                if not isinstance(price_info, dict):
                    continue
                promo   = price_info.get("promo")
                regular = price_info.get("regular")
                price   = promo if promo else regular
                if price and price < best_price:
                    best_price = price
                    best = {
                        "ingredient": term,
                        "found":      True,
                        "name":       p.get("description", term),
                        "upc":        p.get("upc", ""),
                        "brand":      p.get("brand", ""),
                        "price":      price,
                        "promo":      bool(promo),
                        "size":       item.get("size", ""),
                        "image":      (p.get("images") or [{}])[0].get("sizes", [{}])[-1].get("url"),
                    }

        if not best:
            nutrition = get_nutrition_data(term)
            return {"ingredient": term, "found": False, "price": None,
                    "name": None, "upc": None, **nutrition}

        # Enrich with Open Food Facts — barcode lookup first, name fallback
        upc       = best.get("upc", "")
        nutrition = (get_nutrition_by_barcode(upc) or get_nutrition_data(term)) if upc else get_nutrition_data(term)

        best["nutrition_grade"]       = nutrition.get("nutrition_grade")
        best["nutrition_grade_label"] = nutrition.get("nutrition_grade_label")
        best["nutriscore"]            = nutrition.get("nutriscore")
        best["allergens"]             = nutrition.get("allergens", [])
        best["nova_group"]            = nutrition.get("nova_group")
        best["nova_label"]            = nutrition.get("nova_label")
        if not best["image"]:
            best["image"] = nutrition.get("off_image") or nutrition.get("image")

        return best

    except Exception as e:
        return {"ingredient": term, "found": False, "price": None,
                "error": str(e), "nutrition_grade": None}


def _format_hours(hours):
    if not hours:
        return "Hours not available"
    try:
        today = datetime.now().strftime("%A").lower()
        if isinstance(hours, list):
            for entry in hours:
                if isinstance(entry, dict) and entry.get("day", "").lower() == today:
                    if entry.get("open24"):
                        return "Open 24 hours today"
                    o, c = entry.get("open", ""), entry.get("close", "")
                    if o and c:
                        return f"Today: {o} - {c}"
            return "Check store for hours"
        if isinstance(hours, dict):
            dh = hours.get(today, {})
            if isinstance(dh, dict):
                if dh.get("open24"):
                    return "Open 24 hours today"
                o, c = dh.get("open", ""), dh.get("close", "")
                if o and c:
                    return f"Today: {o} - {c}"
        return "Check store for hours"
    except Exception:
        return "Check store for hours"


# --- Routes -------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "FoodFlex API running",
                    "sources": ["Kroger API", "Open Food Facts"]})


@app.route("/api/stores", methods=["GET"])
def get_stores():
    zip_code = request.args.get("zipCode", "")
    if not zip_code:
        return jsonify({"error": "zipCode is required"}), 400
    data = kroger_get("/locations", {
        "filter.zipCode.near": zip_code,
        "filter.radiusInMiles": request.args.get("radius", 10),
        "filter.limit": request.args.get("limit", 5),
    })
    stores = []
    for loc in data.get("data", []):
        if not isinstance(loc, dict):
            continue
        addr = loc.get("address", {}) or {}
        try:
            geo      = loc.get("geolocation", {}) or {}
            latlng   = geo.get("latLng", {}) or {}
            distance = round(float(latlng.get("distance", 0) or 0), 1)
        except Exception:
            distance = 0.0
        stores.append({
            "locationId": loc.get("locationId", ""),
            "name":       loc.get("name", "Kroger"),
            "chain":      loc.get("chain", ""),
            "address":    f"{addr.get('addressLine1','')}, {addr.get('city','')}, {addr.get('state','')}",
            "distance":   distance,
            "phone":      loc.get("phone", ""),
            "hours":      _format_hours(loc.get("hours", {})),
        })
    return jsonify({"stores": stores})


@app.route("/api/prices", methods=["POST"])
def get_prices():
    body         = request.json or {}
    location_ids = body.get("locationIds", [])
    ingredients  = body.get("ingredients", [])
    if not location_ids or not ingredients:
        return jsonify({"error": "locationIds and ingredients are required"}), 400
    results = []
    for loc_id in location_ids:
        store_result = {"locationId": loc_id, "items": []}
        for ingredient in ingredients:
            store_result["items"].append(_search_product(ingredient, loc_id))
        store_result["total"] = round(
            sum(i["price"] for i in store_result["items"] if i.get("price")), 2
        )
        results.append(store_result)
    results.sort(key=lambda x: x["total"] or 99999)
    return jsonify({"results": results})


@app.route("/api/nutrition", methods=["GET"])
def get_nutrition():
    """Standalone nutrition lookup — works without Kroger."""
    barcode = request.args.get("barcode", "")
    term    = request.args.get("term", "")
    if barcode:
        result = get_nutrition_by_barcode(barcode)
        return jsonify(result) if result else (jsonify({"error": "Not found"}), 404)
    if not term:
        return jsonify({"error": "term or barcode required"}), 400
    return jsonify(get_nutrition_data(term))


if __name__ == "__main__":
    print("FoodFlex backend running at http://localhost:5000")
    print("Sources: Kroger API + Open Food Facts")
    print("Endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/stores?zipCode=23501&radius=10")
    print("  POST /api/prices   body: {locationIds, ingredients}")
    print("  GET  /api/nutrition?term=eggs")
    print("  GET  /api/nutrition?barcode=0049000042566")
    app.run(debug=True, port=5000)
