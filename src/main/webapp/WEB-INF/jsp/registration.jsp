<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html>
<head>
    <title>User Registration Form</title>
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
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group.full-width {
            grid-column: 1 / -1;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        label.required::after {
            content: " *";
            color: #e74c3c;
        }
        input[type="text"],
        input[type="email"],
        input[type="tel"],
        input[type="date"],
        select,
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
            font-family: inherit;
        }
        input:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        .checkbox-group,
        .radio-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .checkbox-item,
        .radio-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        input[type="checkbox"],
        input[type="radio"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
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
            margin-top: 10px;
        }
        button:hover {
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
        @media (max-width: 768px) {
            .form-row {
                grid-template-columns: 1fr;
            }
            .container {
                padding: 30px 20px;
            }
        }
    </style>
    <script>
        // Intentionally add a test for console - should NOT produce errors
        console.log('Registration form loaded successfully');
        
        function validateForm(event) {
            const firstName = document.getElementById('firstName').value.trim();
            const email = document.getElementById('email').value.trim();
            
            if (!firstName) {
                alert('Please enter your first name');
                event.preventDefault();
                return false;
            }
            
            if (!email || !email.includes('@')) {
                alert('Please enter a valid email address');
                event.preventDefault();
                return false;
            }
            
            console.log('Form validation passed');
            return true;
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>User Registration</h1>
        <p class="subtitle">Please fill out all required fields</p>
        
        <% if (request.getAttribute("error") != null) { %>
            <div class="error" role="alert">
                ${error}
            </div>
        <% } %>
        
        <form method="post" action="/registration" onsubmit="return validateForm(event)">
            <div class="form-row">
                <div class="form-group">
                    <label for="firstName" class="required">First Name</label>
                    <input type="text" id="firstName" name="firstName" placeholder="John">
                </div>
                
                <div class="form-group">
                    <label for="lastName">Last Name</label>
                    <input type="text" id="lastName" name="lastName" placeholder="Doe">
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="email" class="required">Email Address</label>
                    <input type="email" id="email" name="email" placeholder="john.doe@example.com">
                </div>
                
                <div class="form-group">
                    <label for="phone">Phone Number</label>
                    <input type="tel" id="phone" name="phone" placeholder="+1 555-0100">
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="birthdate">Date of Birth</label>
                    <input type="date" id="birthdate" name="birthdate">
                </div>
                
                <div class="form-group">
                    <label for="country">Country</label>
                    <select id="country" name="country">
                        <option value="">Select a country</option>
                        <option value="us">United States</option>
                        <option value="ca">Canada</option>
                        <option value="uk">United Kingdom</option>
                        <option value="au">Australia</option>
                        <option value="de">Germany</option>
                        <option value="fr">France</option>
                        <option value="jp">Japan</option>
                        <option value="other">Other</option>
                    </select>
                </div>
            </div>
            
            <div class="form-group full-width">
                <label>Gender</label>
                <div class="radio-group">
                    <div class="radio-item">
                        <input type="radio" id="male" name="gender" value="male">
                        <label for="male">Male</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="female" name="gender" value="female">
                        <label for="female">Female</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="other" name="gender" value="other">
                        <label for="other">Other</label>
                    </div>
                    <div class="radio-item">
                        <input type="radio" id="prefer-not" name="gender" value="prefer-not" checked>
                        <label for="prefer-not">Prefer not to say</label>
                    </div>
                </div>
            </div>
            
            <div class="form-group full-width">
                <label>Interests (select all that apply)</label>
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="tech" name="interests" value="technology">
                        <label for="tech">Technology</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="sports" name="interests" value="sports">
                        <label for="sports">Sports</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="music" name="interests" value="music">
                        <label for="music">Music</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="travel" name="interests" value="travel">
                        <label for="travel">Travel</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="reading" name="interests" value="reading">
                        <label for="reading">Reading</label>
                    </div>
                </div>
            </div>
            
            <div class="form-group full-width">
                <label for="comments">Additional Comments</label>
                <textarea id="comments" name="comments" placeholder="Tell us a bit about yourself..."></textarea>
            </div>
            
            <div class="form-group full-width">
                <div class="checkbox-item">
                    <input type="checkbox" id="newsletter" name="newsletter" value="yes">
                    <label for="newsletter">Subscribe to our newsletter</label>
                </div>
            </div>
            
            <button type="submit">Register</button>
        </form>
        
        <a href="/" class="back-link">← Back to Home</a>
    </div>
</body>
</html>

