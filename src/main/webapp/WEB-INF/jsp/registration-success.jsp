<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html>
<head>
    <title>Registration Successful</title>
    <style>
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
            max-width: 500px;
        }
        .checkmark {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: #22c55e;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 48px;
            color: white;
        }
        h1 {
            color: #667eea;
            margin-bottom: 15px;
        }
        p {
            color: #666;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .info strong {
            color: #333;
        }
        .button-group {
            display: flex;
            gap: 10px;
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
        console.log('Registration success page loaded');
    </script>
</head>
<body>
    <div class="success-box">
        <div class="checkmark">✓</div>
        <h1>Registration Successful!</h1>
        <p>Thank you for registering, ${firstName}!</p>
        <div class="info">
            <p><strong>Confirmation sent to:</strong></p>
            <p>${email}</p>
        </div>
        <p>You can now explore our interactive workflow demo.</p>
        <div class="button-group">
            <a href="/workflow">Try Workflow Demo</a>
            <a href="/" class="secondary">Back to Home</a>
        </div>
    </div>
</body>
</html>

