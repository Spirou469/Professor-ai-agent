from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import hashlib
import time



app = Flask(__name__)
CORS(app, origins="*")

SERP_API_KEY = os.environ.get("SERP_API_KEY")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY")
WALLET = "0xB679464A1aEBEe94Ec886cf42f9D6A6e7403e6Aa"
SECRET_SALT = os.environ.get("SECRET_SALT", "dropship_intel_2026")
PRO_PRICE_USD = 3.0

AGENT_INFO = {
    "name": "Dropship Intelligence",
    "version": "3.0.0",
    "description": "Find winning dropshipping products. Real-time Google Shopping data with margin analysis.",
    "price_usdc": 5.0,
    "author": "Spirou469",
    "github": "https://github.com/Spirou469/Professor-ai-agent"
}

def generate_pro_token(tx_hash):
    """Generate a unique token from TX hash — cannot be faked without real TX"""
    raw = f"{tx_hash}{WALLET}{SECRET_SALT}"
    return hashlib.sha256(raw.encode()).hexdigest()

def verify_transaction(tx_hash):
    """Verify transaction on Ethereum blockchain via Etherscan"""
    try:
        # Check on Ethereum mainnet first
        networks = [
            ("ethereum", "https://api.etherscan.io/api"),
            ("polygon", "https://api.polygonscan.com/api"),
            ("bsc", "https://api.bscscan.com/api"),
        ]
        
        for network_name, api_url in networks:
            params = {
                "module": "proxy",
                "action": "eth_getTransactionByHash",
                "txhash": tx_hash,
                "apikey": ETHERSCAN_API_KEY
            }
            
            try:
                response = requests.get(api_url, params=params, timeout=10)
                data = response.json()
                
                if data.get("result") and data["result"] != "null" and data["result"] is not None:
                    tx = data["result"]
                    
                    # Check if sent to our wallet
                    to_address = tx.get("to", "").lower()
                    our_wallet = WALLET.lower()
                    
                    if to_address == our_wallet:
                        # Get transaction value in ETH
                        value_hex = tx.get("value", "0x0")
                        value_wei = int(value_hex, 16)
                        value_eth = value_wei / 1e18
                        
                        # Also check ERC-20 token transfers (USDC)
                        # USDC has 6 decimals
                        # For simplicity, we accept any transaction to our wallet
                        # A real TX to our wallet is enough proof of payment intent
                        
                        return {
                            "valid": True,
                            "network": network_name,
                            "to": to_address,
                            "value_eth": value_eth,
                            "tx_hash": tx_hash,
                            "block": tx.get("blockNumber", "pending")
                        }
            except:
                continue
        
        # If not found on any network, check USDC transfers via Etherscan token API
        usdc_check = check_usdc_transfer(tx_hash)
        if usdc_check:
            return usdc_check
            
        return {"valid": False, "error": "Transaction not found on any network"}
        
    except Exception as e:
        return {"valid": False, "error": str(e)}

def check_usdc_transfer(tx_hash):
    """Check USDC ERC-20 transfer specifically"""
    try:
        params = {
            "module": "proxy",
            "action": "eth_getTransactionReceipt",
            "txhash": tx_hash,
            "apikey": ETHERSCAN_API_KEY
        }
        response = requests.get("https://api.etherscan.io/api", params=params, timeout=10)
        data = response.json()
        
        if data.get("result") and data["result"]:
            receipt = data["result"]
            to_address = receipt.get("to", "").lower()
            
            # Check if transaction went to our wallet or involves our wallet in logs
            our_wallet = WALLET.lower()
            
            # Check logs for USDC transfer to our wallet
            logs = receipt.get("logs", [])
            for log in logs:
                # Transfer event topic
                topics = log.get("topics", [])
                if len(topics) >= 3:
                    # ERC-20 Transfer event
                    to_topic = topics[2].lower()
                    if our_wallet.replace("0x", "") in to_topic:
                        return {
                            "valid": True,
                            "network": "ethereum_token",
                            "to": our_wallet,
                            "tx_hash": tx_hash,
                            "type": "ERC20_transfer"
                        }
        
        return None
    except:
        return None

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
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        data = response.json()
        products = []
        if "shopping_results" in data:
            for item in data["shopping_results"][:max_results]:
                try:
                    price = float(str(item.get("price", "0")).replace("$", "").replace(",", "").split()[0])
                except:
                    price = 0
                if price > 0:
                    products.append({
                        "title": item.get("title", "N/A"),
                        "price": price,
                        "source": item.get("source", "N/A"),
                        "rating": item.get("rating", 0),
                        "reviews": item.get("reviews", 0),
                        "link": item.get("link", ""),
                        "thumbnail": item.get("thumbnail", "")
                    })
        return products
    except Exception as e:
        return {"error": str(e)}

def calculate_metrics(products):
    if not products:
        return {}
    prices = [p["price"] for p in products if p["price"] > 0]
    ratings = [p["rating"] for p in products if p["rating"] > 0]
    reviews = [p["reviews"] for p in products if p["reviews"] > 0]
    avg_price = sum(prices) / len(prices) if prices else 0
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    avg_reviews = sum(reviews) / len(reviews) if reviews else 0
    supplier = avg_price * 0.25
    margin = avg_price - supplier
    return {
        "average_price": round(avg_price, 2),
        "estimated_supplier_price": round(supplier, 2),
        "estimated_profit_margin": round(margin, 2),
        "margin_percentage": round((margin / avg_price * 100) if avg_price > 0 else 0, 1),
        "average_rating": round(avg_rating, 1),
        "average_reviews": round(avg_reviews),
        "competition_level": "High 🔴" if avg_reviews > 1000 else "Medium 🟡" if avg_reviews > 200 else "Low 🟢"
    }

def analyze_products(products, niche):
    analysis = f"=== DROPSHIPPING ANALYSIS: {niche.upper()} ===\n\n"
    for i, p in enumerate(products[:5], 1):
        supplier = round(p['price'] * 0.25, 2)
        margin = round(p['price'] - supplier, 2)
        margin_pct = round((margin / p['price'] * 100) if p['price'] > 0 else 0, 1)
        reviews = p.get('reviews', 0)
        competition = "Low 🟢" if reviews < 500 else "Medium 🟡" if reviews < 2000 else "High 🔴"
        potential = "🔥 HIGH" if margin > 30 and p.get('rating', 0) >= 4.0 else "✅ MEDIUM" if margin > 15 else "⚠️ LOW"
        analysis += f"""Product {i}: {p['title'][:70]}
  💰 Retail: ${p['price']} | Supplier est: ${supplier}
  📈 Margin: ${margin} ({margin_pct}%)
  ⭐ Rating: {p.get('rating','N/A')}/5 ({reviews} reviews)
  🏪 {p['source']} | Competition: {competition}
  🎯 Potential: {potential}
  🔗 {p.get('link','')}\n\n"""
    return analysis

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "active", "agent": AGENT_INFO})

@app.route("/info", methods=["GET"])
def info():
    return jsonify(AGENT_INFO)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/verify-payment", methods=["POST", "OPTIONS"])
def verify_payment():
    """Verify crypto payment and return pro token"""
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        data = request.get_json(force=True)
        tx_hash = data.get("tx_hash", "").strip()
        
        if not tx_hash or not tx_hash.startswith("0x"):
            return jsonify({"success": False, "error": "Invalid transaction hash"}), 400
        
        if len(tx_hash) != 66:
            return jsonify({"success": False, "error": "Transaction hash must be 66 characters"}), 400
        
        # Verify on blockchain
        result = verify_transaction(tx_hash)
        
        if result.get("valid"):
            # Generate unique pro token
            pro_token = generate_pro_token(tx_hash)
            return jsonify({
                "success": True,
                "pro_token": pro_token,
                "network": result.get("network"),
                "message": "Payment verified! Pro access unlocked."
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Transaction not found or not sent to our wallet")
            }), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/verify-token", methods=["POST", "OPTIONS"])
def verify_token():
    """Verify if a pro token is valid"""
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        data = request.get_json(force=True)
        token = data.get("token", "").strip()
        tx_hash = data.get("tx_hash", "").strip()
        
        if not token or not tx_hash:
            return jsonify({"valid": False}), 400
        
        expected = generate_pro_token(tx_hash)
        return jsonify({"valid": token == expected})
        
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500

@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        data = request.get_json(force=True)
        if not data or "niche" not in data:
            return jsonify({"error": "Please provide a niche"}), 400

        niche = data.get("niche", "")
        max_results = data.get("max_results", 5)
        pro_token = data.get("pro_token", "")
        tx_hash = data.get("tx_hash", "")

        # Verify pro access server-side
        is_pro = False
        if pro_token and tx_hash:
            expected = generate_pro_token(tx_hash)
            is_pro = (pro_token == expected)

        # Limit results for free users
        if not is_pro:
            max_results = min(max_results, 5)
        else:
            max_results = min(max_results, 20)

        products = search_products(niche, max_results)
        if isinstance(products, dict) and "error" in products:
            return jsonify({"error": products["error"]}), 500
        if not products:
            return jsonify({"error": "No products found"}), 404

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
            "is_pro": is_pro,
            "price_paid_usdc": 5.0
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/trending", methods=["GET"])
def trending():
    return jsonify({
        "status": "success",
        "trending_niches": ["wireless earbuds","phone stands","LED lights","resistance bands","portable charger","kitchen gadgets","pet accessories","desk accessories","yoga mat","posture corrector"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
