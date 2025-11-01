<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html>
<head>
    <title>Workflow - Step 2</title>
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
            max-width: 600px;
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
        .step.completed .step-circle {
            background: #22c55e;
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
        .selected-product {
            background: #f0f4ff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border: 2px solid #667eea;
        }
        .selected-product h3 {
            color: #667eea;
            margin-bottom: 5px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        input[type="number"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        .quantity-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-top: 10px;
        }
        .qty-btn {
            width: 40px;
            height: 40px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 5px;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .qty-btn:hover {
            background: #667eea;
            color: white;
        }
        button[type="submit"] {
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
            margin-top: 10px;
        }
        button[type="submit"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
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
    </style>
    <script>
        console.log('Workflow step 2 loaded');
        
        function updateQuantity(change) {
            const input = document.getElementById('quantity');
            let value = parseInt(input.value) || 1;
            value = Math.max(1, value + change);
            input.value = value;
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="progress-bar">
            <div class="step completed">
                <div class="step-circle">✓</div>
                <div class="step-label">Select Product</div>
            </div>
            <div class="step active">
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

        <h1>Step 2: Select Quantity</h1>
        <p class="subtitle">How many would you like?</p>
        
        <% if (request.getAttribute("error") != null) { %>
            <div class="error" role="alert">${error}</div>
        <% } %>
        
        <div class="selected-product">
            <h3>Selected Product:</h3>
            <p style="text-transform: capitalize; font-size: 1.2em; color: #333;">${product}</p>
        </div>
        
        <form method="post" action="/workflow/step3">
            <input type="hidden" name="product" value="${product}">
            
            <div class="form-group">
                <label for="quantity">Quantity</label>
                <input type="number" id="quantity" name="quantity" value="1" min="1" max="99">
                <div class="quantity-controls">
                    <button type="button" class="qty-btn" onclick="updateQuantity(-1)">-</button>
                    <span>Click buttons or type a number</span>
                    <button type="button" class="qty-btn" onclick="updateQuantity(1)">+</button>
                </div>
            </div>
            
            <button type="submit">Continue to Review</button>
        </form>
        
        <a href="/workflow" class="back-link">← Back to product selection</a>
    </div>
</body>
</html>

