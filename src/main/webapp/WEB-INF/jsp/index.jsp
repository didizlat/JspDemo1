<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html>
<head>
    <title>JSP Demo - Home</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        a {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        a:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        @media (max-width: 768px) {
            body {
                margin: 20px;
                padding: 10px;
            }
            h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>${message}</h1>
        <p>This is a working JSP application running on Spring Boot with embedded Tomcat.</p>
        <p style="margin-top: 20px;">Explore our interactive demos:</p>
        <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 20px;">
            <a href="/registration">📝 User Registration Form</a>
            <a href="/workflow">🛒 Multi-Step Workflow Demo</a>
            <a href="/login">🔐 Simple Login Form</a>
        </div>
    </div>
</body>
</html>

