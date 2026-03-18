# GrocerySmart — Kroger API Integration

## What you have
A full-stack grocery price comparison app connected to **Kroger's live product database** (300k+ products across Kroger, Ralph's, Fred Meyer, Harris Teeter, and more).

---

## Quick Start (15 minutes)

### Step 1: Get Free Kroger API Keys
1. Go to https://developer.kroger.com/manage/apps/register
2. Create an account and register a new app
3. Set scope to `product.compact`
4. Set redirect URI to `http://localhost:8000/callback` (not used for this app but required)
5. Copy your **Client ID** and **Client Secret**

### Step 2: Set Up the Backend
```bash
# Install dependencies
pip install flask flask-cors requests python-dotenv

# Create your credentials file
echo "KROGER_CLIENT_ID=paste_your_id_here" > .env
echo "KROGER_CLIENT_SECRET=paste_your_secret_here" >> .env

# Run the server
python backend.py
```
You should see: `🚀 GrocerySmart backend running at http://localhost:5000`

### Step 3: Open the Frontend
Open `index.html` in your browser (or run `python -m http.server 8080` and visit localhost:8080).

---

## API Endpoints

### GET /api/health
Test that your server is running.
```
curl http://localhost:5000/api/health
```

### GET /api/stores
Find Kroger-family stores near a zip code.
```
curl "http://localhost:5000/api/stores?zipCode=90210&radius=10&limit=5"
```
Returns: name, address, chain, distance, hours for each store.

### POST /api/prices
Get price comparison across stores for your ingredient list.
```bash
curl -X POST http://localhost:5000/api/prices \
  -H "Content-Type: application/json" \
  -d '{
    "locationIds": ["01400376", "01400943"],
    "ingredients": ["chicken breast", "eggs", "whole milk"]
  }'
```
Returns: sorted list of stores with real product names, prices, promo flags, and images.

---

## Kroger API Coverage
Kroger's API covers these chains:
- Kroger
- Ralphs
- Fred Meyer
- Harris Teeter
- King Soopers
- Smith's
- Mariano's
- Pick 'n Save
- QFC
- Dillons
- Baker's
- Gerbes
- And more

This covers **~2,800 stores** across the US — a massive head start.

---

## Expanding to Other Stores

| Store       | Data Source                | Difficulty |
|-------------|---------------------------|------------|
| Walmart     | walmart.com scraping       | Medium ⚠️ |
| Aldi        | No public API — manual    | Hard ❌   |
| Instacart   | Partner API (apply)        | Medium     |
| Flipp.com   | Weekly ads API (apply)     | Easy ✅    |
| Target      | No public API — scraping  | Medium     |

**Best path to multi-store:** Apply to Instacart's developer program.
They aggregate pricing from 1,000+ retailers including Costco, Aldi, and Whole Foods.
→ https://www.instacart.com/business/developers

---

## Deployment (Go Live)

### Backend (free options)
- **Railway.app** — push to GitHub, auto-deploys, free tier
- **Render.com** — similar, reliable free tier
- **Fly.io** — great for small APIs

### Frontend
- **GitHub Pages** — drop index.html in a repo, enable Pages, done
- **Netlify** — drag and drop the HTML file

### Update the API URL
In `index.html`, change:
```javascript
const API = "http://localhost:5000/api";
```
to your deployed backend URL, e.g.:
```javascript
const API = "https://grocerysmart-api.railway.app/api";
```

---

## YouTube Content Angles
1. "I Built a Grocery Price Comparison App in 1 Day" (tutorial)
2. "How Kroger's Secret API Can Save You $50/Month" (educational)
3. "Building a SaaS on Top of Free APIs" (business)
4. "I Tested 5 Grocery Stores With My App — Results Were Surprising" (results/review)

---

## Monetization (Hormozi Model)
- **Free core app** → traffic & trust
- **Affiliate**: Kroger Pay links = commission on orders
- **Premium** ($4.99/mo): meal planning, price alerts, multi-store (Instacart)
- **Sponsor**: Kroger itself may pay to promote via their developer partner program
