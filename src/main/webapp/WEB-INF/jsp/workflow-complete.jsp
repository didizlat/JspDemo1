<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html>
<head>
    <title>Order Complete</title>
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
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .success-box {
            background: white;
            padding: 60px 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 600px;
        }
        .checkmark {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: #22c55e;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 60px;
            color: white;
            animation: scaleIn 0.5s ease-out;
        }
        @keyframes scaleIn {
            from {
                transform: scale(0);
            }
            to {
                transform: scale(1);
            }
        }
        h1 {
            color: #22c55e;
            margin-bottom: 15px;
            font-size: 2.5em;
        }
        p {
            color: #666;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .order-summary {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin: 30px 0;
        }
        .order-summary h3 {
            color: #333;
            margin-bottom: 20px;
        }
        .summary-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .summary-row:last-child {
            border-bottom: none;
        }
        .order-number {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
            margin: 20px 0;
            font-weight: bold;
        }
        .button-group {
            display: flex;
            gap: 15px;
            margin-top: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }
        a {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        a:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        a.secondary {
            background: #6c757d;
        }
    </style>
    <script>
        console.log('Workflow completed successfully!');
    </script>
</head>
<body>
    <div class="success-box">
        <div class="checkmark">✓</div>
        <h1>Order Complete!</h1>
        <p>Thank you for your order</p>
        
        <div class="order-number">Order #${(int)(Math.random() * 90000) + 10000}</div>
        
        <div class="order-summary">
            <h3>Order Summary</h3>
            <div class="summary-row">
                <span>Product:</span>
                <strong style="text-transform: capitalize;">${product}</strong>
            </div>
            <div class="summary-row">
                <span>Quantity:</span>
                <strong>${quantity}</strong>
            </div>
            <div class="summary-row">
                <span>Status:</span>
                <strong style="color: #22c55e;">Confirmed</strong>
            </div>
        </div>
        
        <p style="color: #999; font-size: 0.95em;">
            A confirmation email has been sent to your registered email address.
        </p>
        
        <div class="button-group">
            <a href="/workflow">Start New Order</a>
            <a href="/registration">New Registration</a>
            <a href="/" class="secondary">Back to Home</a>
        </div>
    </div>
</body>
</html>

