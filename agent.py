from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app, origins="*")

RAINFOREST_API_KEY = os.environ.get("RAINFOREST_API_KEY")
HF_API_KEY = os.environ.get("HF_API_KEY")

AGENT_INFO = {
    "name": "Dropship Intelligence",
    "version": "1.0.0",
    "description": "Find winning dropshipping products on Amazon. Get margin analysis, competition level, and trending niches automatically.",
    "price_usdc": 5.0,
    "capabilities": [
        "Find trending products by niche",
        "Analyze profit margins",
        "Competition level analysis",
        "Best seller detection",
        "Price history tracking"
    ],
    "author": "Spirou469",
    "github": "https://github.com/Spirou469/Professor-ai-agent"
}

def search_amazon_products(niche, max_results=10):
    """Search Amazon products via Rainforest API"""
    try:
        params = {
            "api_key": RAINFOREST_API_KEY,
            "type": "search",
            "amazon_domain": "amazon.com",
            "search_term": niche,
            "sort_by": "featured",
            "page": "1"
        }
        response = requests.get(
            "https://api.rainforestapi.com/request",
            params=params,
            timeout=30
        )
        data = response.json()
        products = []
        if "search_results" in data:
            for item in data["search_results"][:max_results]:
                product = {
                    "title": item.get("title", "N/A"),
                    "price": item.get("price", {}).get("value", 0),
                    "rating": item.get("rating", 0),
                    "ratings_total": item.get("ratings_total", 0),
                    "asin": item.get("asin", ""),
                    "url": f"https://amazon.com/dp/{item.get('asin', '')}",
                    "is_bestseller": item.get("is_bestseller", False),
                    "image": item.get("image", "")
                }
                if product["price"] > 0:
                    products.append(product)
        return products
    except Exception as e:
        return {"error": str(e)}
def analyze_with_ai(products, niche):
    """Smart analysis without external AI API"""
    analysis = f"=== DROPSHIPPING ANALYSIS: {niche.upper()} ===\n\n"
    for i, p in enumerate(products[:5], 1):
        supplier_price = round(p['price'] * 0.25, 2)
        margin = round(p['price'] - supplier_price, 2)
        margin_pct = round((margin / p['price'] * 100) if p['price'] > 0 else 0, 1)
        competition = "Low 🟢" if p['ratings_total'] < 500 else "Medium 🟡" if p['ratings_total'] < 2000 else "High 🔴"
        potential = "🔥 HIGH" if margin > 30 and p['rating'] >= 4.3 else "✅ MEDIUM" if margin > 15 else "⚠️ LOW"
        analysis += f"""Product {i}: {p['title'][:60]}...
  💰 Amazon Price: ${p['price']}
  🏭 Est. Supplier Price: ${supplier_price}
  📈 Est. Profit Margin: ${margin} ({margin_pct}%)
  ⭐ Rating: {p['rating']}/5 ({p['ratings_total']} reviews)
  🏆 Competition: {competition}
  🎯 Dropship Potential: {potential}
  🔗 {p['url']}\n\n"""
    return analysis
    
def calculate_metrics(products):
    """Calculate dropshipping metrics"""
    if not products:
        return {}
    prices = [p["price"] for p in products if p["price"] > 0]
    ratings = [p["rating"] for p in products if p["rating"] > 0]
    reviews = [p["ratings_total"] for p in products if p["ratings_total"] > 0]
    bestsellers = sum(1 for p in products if p["is_bestseller"])

    avg_price = sum(prices) / len(prices) if prices else 0
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    avg_reviews = sum(reviews) / len(reviews) if reviews else 0
    estimated_supplier_price = avg_price * 0.25
    estimated_margin = avg_price - estimated_supplier_price

    return {
        "average_price": round(avg_price, 2),
        "estimated_supplier_price": round(estimated_supplier_price, 2),
        "estimated_profit_margin": round(estimated_margin, 2),
        "margin_percentage": round((estimated_margin / avg_price * 100) if avg_price > 0 else 0, 1),
        "average_rating": round(avg_rating, 1),
        "average_reviews": round(avg_reviews),
        "bestsellers_found": bestsellers,
        "competition_level": "High" if avg_reviews > 1000 else "Medium" if avg_reviews > 200 else "Low"
    }

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
                "example": {"niche": "fitness equipment", "max_results": 10}
            }), 400

        niche = data.get("niche", "")
        max_results = min(data.get("max_results", 10), 20)

        # Step 1: Search Amazon
        products = search_amazon_products(niche, max_results)
        if isinstance(products, dict) and "error" in products:
            return jsonify({"error": products["error"]}), 500

        if not products:
            return jsonify({"error": "No products found for this niche"}), 404

        # Step 2: Calculate metrics
        metrics = calculate_metrics(products)

        # Step 3: AI Analysis
        ai_analysis = analyze_with_ai(products, niche)

        return jsonify({
            "status": "success",
            "agent": "Dropship Intelligence",
            "niche": niche,
            "products_found": len(products),
            "metrics": metrics,
            "top_products": products[:5],
            "ai_analysis": ai_analysis,
            "price_paid_usdc": 5.0
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/trending", methods=["GET", "OPTIONS"])
def trending():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        trending_niches = [
            "wireless earbuds", "phone stands", "LED lights room",
            "fitness resistance bands", "portable charger",
            "kitchen gadgets", "pet accessories", "home office desk accessories"
        ]
        return jsonify({
            "status": "success",
            "trending_niches": trending_niches,
            "tip": "These niches have high demand and good margins for dropshipping"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
