<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html>
<head>
    <title>Workflow - Step 3</title>
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
        .review-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .review-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .review-row:last-child {
            border-bottom: none;
            font-weight: bold;
            font-size: 1.2em;
            color: #667eea;
            margin-top: 10px;
        }
        .review-label {
            color: #666;
        }
        .review-value {
            color: #333;
            font-weight: 500;
        }
        button {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
            margin-bottom: 10px;
        }
        button[type="submit"] {
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
        }
        button[type="submit"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(34, 197, 94, 0.4);
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
        console.log('Workflow step 3 (review) loaded');
    </script>
</head>
<body>
    <div class="container">
        <div class="progress-bar">
            <div class="step completed">
                <div class="step-circle">✓</div>
                <div class="step-label">Select Product</div>
            </div>
            <div class="step completed">
                <div class="step-circle">✓</div>
                <div class="step-label">Quantity</div>
            </div>
            <div class="step active">
                <div class="step-circle">3</div>
                <div class="step-label">Review</div>
            </div>
            <div class="step">
                <div class="step-circle">4</div>
                <div class="step-label">Complete</div>
            </div>
        </div>

        <h1>Step 3: Review Your Order</h1>
        <p class="subtitle">Please confirm your selection</p>
        
        <div class="review-card">
            <div class="review-row">
                <span class="review-label">Product:</span>
                <span class="review-value" style="text-transform: capitalize;">${product}</span>
            </div>
            <div class="review-row">
                <span class="review-label">Quantity:</span>
                <span class="review-value">${quantity}</span>
            </div>
            <div class="review-row">
                <span class="review-label">Total Items:</span>
                <span class="review-value">${quantity}</span>
            </div>
        </div>
        
        <form method="post" action="/workflow/complete">
            <input type="hidden" name="product" value="${product}">
            <input type="hidden" name="quantity" value="${quantity}">
            <button type="submit">Confirm and Complete Order</button>
        </form>
        
        <a href="/workflow" class="back-link">← Start over</a>
    </div>
</body>
</html>

