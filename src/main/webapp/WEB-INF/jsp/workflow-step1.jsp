<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html>
<head>
    <title>Workflow - Step 1</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .progress-bar {
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            position: relative;
        }
        .progress-bar::before {
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: #e0e0e0;
            z-index: 0;
        }
        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 1;
        }
        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .step.active .step-circle {
            background: #667eea;
            color: white;
        }
        .step-label {
            font-size: 12px;
            color: #666;
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .product-card {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .product-card:hover {
            border-color: #667eea;
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .product-card.selected {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .product-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
        .product-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .product-price {
            color: #667eea;
            font-size: 1.2em;
            font-weight: bold;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border: 1px solid #fcc;
            text-align: center;
        }
        .back-link {
            display: block;
            text-align: center;
            margin-top: 20px;
            color: #667eea;
            text-decoration: none;
        }
        @media (max-width: 768px) {
            .product-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    <script>
        console.log('Workflow step 1 loaded');
        
        function selectProduct(productName) {
            document.querySelectorAll('.product-card').forEach(card => {
                card.classList.remove('selected');
            });
            event.currentTarget.classList.add('selected');
            document.getElementById('selectedProduct').value = productName;
            document.getElementById('continueBtn').disabled = false;
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="progress-bar">
            <div class="step active">
                <div class="step-circle">1</div>
                <div class="step-label">Select Product</div>
            </div>
            <div class="step">
                <div class="step-circle">2</div>
                <div class="step-label">Quantity</div>
            </div>
            <div class="step">
                <div class="step-circle">3</div>
                <div class="step-label">Review</div>
            </div>
            <div class="step">
                <div class="step-circle">4</div>
                <div class="step-label">Complete</div>
            </div>
        </div>

        <h1>Step 1: Select a Product</h1>
        <p class="subtitle">Choose the product you'd like to purchase</p>
        
        <% if (request.getAttribute("error") != null) { %>
            <div class="error" role="alert">${error}</div>
        <% } %>
        
        <form method="post" action="/workflow/step2">
            <input type="hidden" id="selectedProduct" name="product" value="">
            
            <div class="product-grid">
                <div class="product-card" onclick="selectProduct('laptop')">
                    <div class="product-icon">💻</div>
                    <div class="product-name">Laptop</div>
                    <div class="product-price">$999</div>
                </div>
                
                <div class="product-card" onclick="selectProduct('phone')">
                    <div class="product-icon">📱</div>
                    <div class="product-name">Smartphone</div>
                    <div class="product-price">$699</div>
                </div>
                
                <div class="product-card" onclick="selectProduct('tablet')">
                    <div class="product-icon">📟</div>
                    <div class="product-name">Tablet</div>
                    <div class="product-price">$499</div>
                </div>
                
                <div class="product-card" onclick="selectProduct('watch')">
                    <div class="product-icon">⌚</div>
                    <div class="product-name">Smartwatch</div>
                    <div class="product-price">$299</div>
                </div>
            </div>
            
            <button type="submit" id="continueBtn" disabled>Continue to Next Step</button>
        </form>
        
        <a href="/" class="back-link">← Cancel and go home</a>
    </div>
</body>
</html>

