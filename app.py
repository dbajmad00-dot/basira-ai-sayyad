
from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>بصيرة الصياد AI</title>
<style>
body{background:#101827;color:white;font-family:Arial;padding:18px}
.box{background:#1d2a3d;padding:20px;border-radius:15px;margin:15px 0}
h1{color:#39d5b0;text-align:center}
select,button{width:100%;padding:14px;margin-top:12px;
border:0;border-radius:9px;font-size:17px}
button{background:#16b99a;color:#071b1a;font-weight:bold}
.result{font-size:23px;text-align:center;padding:18px}
small{color:#aab8ca}
</style>
</head>
<body>
<h1>🎯 بصيرة الصياد AI</h1>
<p style="text-align:center">محلل أسواق Binance المباشر</p>

<div class="box">
<label>اختر العملة</label>
<select id="symbol">
<option>BTCUSDT</option>
<option>ETHUSDT</option>
<option>BNBUSDT</option>
<option>DOGEUSDT</option>
<option>SOLUSDT</option>
</select>

<label>الإطار الزمني</label>
<select id="interval">
<option value="1m">دقيقة</option>
<option value="5m">5 دقائق</option>
<option value="15m">15 دقيقة</option>
<option value="1h">ساعة</option>
</select>

<button onclick="analyze()">ابدأ التحليل الآن</button>
</div>

<div class="box">
<div id="result" class="result">جاهز للتحليل</div>
<div id="details">اختر العملة واضغط تحليل</div>
</div>

<script>
async function analyze(){
 const r=document.getElementById('result');
 const d=document.getElementById('details');
 r.innerText='⏳ جاري تحليل السوق...';
 d.innerText='';
 try{
  const s=document.getElementById('symbol').value;
  const t=document.getElementById('interval').value;
  const response=await fetch('/analyze?symbol='+s+'&interval='+t);
  const data=await response.json();
  if(!response.ok) throw new Error(data.error || 'تعذر التحليل');
  r.innerText=data.signal;
  d.innerHTML='العملة: '+data.symbol+
  '<br>السعر: '+data.price+
  '<br>RSI: '+data.rsi+
  '<br>EMA 20: '+data.ema+
  '<br>الاتجاه: '+data.trend+
  '<br><br>السبب: '+data.reason;
 }catch(e){
  r.innerText='حدث خطأ';
  d.innerText=e.message;
 }
}
</script>
</body>
</html>
"""

def ema(values, period=20):
    k = 2 / (period + 1)
    result = values[0]
    for price in values[1:]:
        result = price * k + result * (1-k)
    return result

def calculate_rsi(prices, period=14):
    changes = [prices[i]-prices[i-1]
               for i in range(1, len(prices))]
    gains = [max(x, 0) for x in changes]
    losses = [max(-x, 0) for x in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/analyze")
def analyze():
    symbol = request_symbol = __import__('flask').request.args.get(
        "symbol", "BTCUSDT").upper()
    interval = __import__('flask').request.args.get(
        "interval", "1m")

    allowed_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT",
                       "DOGEUSDT", "SOLUSDT"]
    allowed_intervals = ["1m", "5m", "15m", "1h"]

    if symbol not in allowed_symbols or interval not in allowed_intervals:
        return jsonify({"error": "اختيار غير صحيح"}), 400

    try:
        url = "https://api.binance.com/api/v3/klines"
        response = requests.get(
            url,
            params={"symbol": symbol, "interval": interval,
                    "limit": 100},
            timeout=15
        )
        response.raise_for_status()
        candles = response.json()

        if not isinstance(candles, list) or len(candles) < 30:
            raise ValueError("بيانات السوق غير كافية")

        prices = [float(c[4]) for c in candles]
        current = prices[-1]
        average = ema(prices[-20:], 20)
        rsi = calculate_rsi(prices)

        if current > average and 50 < rsi < 70:
            signal = "🟢 شراء محتمل"
            trend = "صاعد"
            reason = "السعر فوق EMA20 و RSI إيجابي"
        elif current < average and 30 < rsi < 50:
            signal = "🔴 بيع محتمل"
            trend = "هابط"
            reason = "السعر تحت EMA20 و RSI سلبي"
        else:
            signal = "🟡 انتظار"
            trend = "غير واضح"
            reason = "الإشارات غير متوافقة"

        return jsonify({
            "symbol": symbol,
            "price": current,
            "ema": round(average, 6),
            "rsi": round(rsi, 2),
            "signal": signal,
            "trend": trend,
            "reason": reason
        })

    except Exception as e:
        return jsonify({"error": "تعذر جلب البيانات: " + str(e)}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
