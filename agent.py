from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app, origins="*")

SERP_API_KEY = os.environ.get("SERP_API_KEY")

AGENT_INFO = {
    "name": "Dropship Intelligence",
    "version": "2.0.0",
    "description": "Find winning dropshipping products. Get margin analysis, competition level, and trending niches automatically.",
    "price_usdc": 5.0,
    "capabilities": [
        "Find trending products by niche",
        "Analyze profit margins",
        "Competition level analysis",
        "Google Shopping data",
        "Price comparison across stores"
    ],
    "author": "Spirou469",
    "github": "https://github.com/Spirou469/Professor-ai-agent"
}

def search_products(niche, max_results=10):
    """Search products via SerpAPI Google Shopping"""
    try:
        params = {
            "api_key": SERP_API_KEY,
            "engine": "google_shopping",
            "q": niche,
            "num": max_results,
            "gl": "us",
            "hl": "en"
        }
        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=30
        )
        data = response.json()
        products = []
        if "shopping_results" in data:
            for item in data["shopping_results"][:max_results]:
                price_str = item.get("price", "0")
                try:
                    price = float(price_str.replace("$", "").replace(",", "").split()[0])
                except:
                    price = 0
                product = {
                    "title": item.get("title", "N/A"),
                    "price": price,
                    "source": item.get("source", "N/A"),
                    "rating": item.get("rating", 0),
                    "reviews": item.get("reviews", 0),
                    "link": item.get("link", ""),
                    "thumbnail": item.get("thumbnail", "")
                }
                if product["price"] > 0:
                    products.append(product)
        return products
    except Exception as e:
        return {"error": str(e)}

def calculate_metrics(products):
    """Calculate dropshipping metrics"""
    if not products:
        return {}
    prices = [p["price"] for p in products if p["price"] > 0]
    ratings = [p["rating"] for p in products if p["rating"] > 0]
    reviews = [p["reviews"] for p in products if p["reviews"] > 0]

    avg_price = sum(prices) / len(prices) if prices else 0
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    avg_reviews = sum(reviews) / len(reviews) if reviews else 0
    supplier_price = avg_price * 0.25
    margin = avg_price - supplier_price

    return {
        "average_price": round(avg_price, 2),
        "estimated_supplier_price": round(supplier_price, 2),
        "estimated_profit_margin": round(margin, 2),
        "margin_percentage": round((margin / avg_price * 100) if avg_price > 0 else 0, 1),
        "average_rating": round(avg_rating, 1),
        "average_reviews": round(avg_reviews),
        "competition_level": "High 🔴" if avg_reviews > 1000 else "Medium 🟡" if avg_reviews > 200 else "Low 🟢"
    }

def analyze_products(products, niche):
    """Smart analysis without external AI API"""
    analysis = f"=== DROPSHIPPING ANALYSIS: {niche.upper()} ===\n\n"
    for i, p in enumerate(products[:5], 1):
        supplier_price = round(p['price'] * 0.25, 2)
        margin = round(p['price'] - supplier_price, 2)
        margin_pct = round((margin / p['price'] * 100) if p['price'] > 0 else 0, 1)
        reviews = p.get('reviews', 0)
        competition = "Low 🟢" if reviews < 500 else "Medium 🟡" if reviews < 2000 else "High 🔴"
        potential = "🔥 HIGH" if margin > 30 and p.get('rating', 0) >= 4.0 else "✅ MEDIUM" if margin > 15 else "⚠️ LOW"
        analysis += f"""Product {i}: {p['title'][:70]}
  💰 Retail Price: ${p['price']}
  🏭 Est. Supplier Price: ${supplier_price}
  📈 Est. Profit Margin: ${margin} ({margin_pct}%)
  ⭐ Rating: {p.get('rating', 'N/A')}/5 ({reviews} reviews)
  🏪 Source: {p['source']}
  🏆 Competition: {competition}
  🎯 Dropship Potential: {potential}
  🔗 {p['link']}\n\n"""
    return analysis

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "active", "agent": AGENT_INFO})

@app.route("/info", methods=["GET"])
def info():
    return jsonify(AGENT_INFO)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "agent": "Dropship Intelligence"})

@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        data = request.get_json(force=True)
        if not data or "niche" not in data:
            return jsonify({
                "error": "Please provide a niche",
                "example": {"niche": "wireless earbuds", "max_results": 10}
            }), 400

        niche = data.get("niche", "")
        max_results = min(data.get("max_results", 10), 20)

        products = search_products(niche, max_results)
        if isinstance(products, dict) and "error" in products:
            return jsonify({"error": products["error"]}), 500
        if not products:
            return jsonify({"error": "No products found for this niche"}), 404

        metrics = calculate_metrics(products)
        analysis = analyze_products(products, niche)

        return jsonify({
            "status": "success",
            "agent": "Dropship Intelligence",
            "niche": niche,
            "products_found": len(products),
            "metrics": metrics,
            "top_products": products[:5],
            "analysis": analysis,
            "price_paid_usdc": 5.0
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/trending", methods=["GET", "OPTIONS"])
def trending():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    return jsonify({
        "status": "success",
        "trending_niches": [
            "wireless earbuds",
            "phone stands",
            "LED lights room",
            "fitness resistance bands",
            "portable charger",
            "kitchen gadgets",
            "pet accessories",
            "home office desk accessories"
        ],
        "tip": "These niches have high demand and good margins for dropshipping"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
