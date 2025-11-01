<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Registrations</title>
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
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            position: sticky;
            top: 0;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
        }
        .badge-yes {
            background: #d4edda;
            color: #155724;
        }
        .badge-no {
            background: #f8d7da;
            color: #721c24;
        }
        .nav-links {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .nav-links a {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            transition: transform 0.2s;
        }
        .nav-links a:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        .nav-links a.secondary {
            background: #6c757d;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
    </style>
    <script>
        console.log('Admin registrations page loaded');
    </script>
</head>
<body>
    <div class="container">
        <div class="nav-links">
            <a href="/admin/registrations">👥 Registrations</a>
            <a href="/admin/orders">📦 Orders</a>
            <a href="/h2-console" target="_blank">🗄️ H2 Console</a>
            <a href="/" class="secondary">← Home</a>
        </div>
        
        <h1>Registration Database</h1>
        <p class="subtitle">View all user registrations</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">${registrations.size()}</div>
                <div class="stat-label">Total Registrations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">
                    <c:set var="newsletterCount" value="0"/>
                    <c:forEach var="reg" items="${registrations}">
                        <c:if test="${reg.newsletter}">
                            <c:set var="newsletterCount" value="${newsletterCount + 1}"/>
                        </c:if>
                    </c:forEach>
                    ${newsletterCount}
                </div>
                <div class="stat-label">Newsletter Subscribers</div>
            </div>
        </div>
        
        <c:choose>
            <c:when test="${empty registrations}">
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <h2>No Registrations Yet</h2>
                    <p>Go to <a href="/registration" style="color: #667eea;">Registration Form</a> to create test data</p>
                </div>
            </c:when>
            <c:otherwise>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Phone</th>
                            <th>Country</th>
                            <th>Interests</th>
                            <th>Newsletter</th>
                            <th>Registered</th>
                        </tr>
                    </thead>
                    <tbody>
                        <c:forEach var="reg" items="${registrations}">
                            <tr>
                                <td>#${reg.id}</td>
                                <td><strong>${reg.firstName} ${reg.lastName}</strong></td>
                                <td>${reg.email}</td>
                                <td>${reg.phone}</td>
                                <td style="text-transform: uppercase;">${reg.country}</td>
                                <td style="font-size: 0.9em;">${reg.interests}</td>
                                <td>
                                    <c:choose>
                                        <c:when test="${reg.newsletter}">
                                            <span class="badge badge-yes">✓ Yes</span>
                                        </c:when>
                                        <c:otherwise>
                                            <span class="badge badge-no">✗ No</span>
                                        </c:otherwise>
                                    </c:choose>
                                </td>
                                <td style="font-size: 0.85em;">
                                    ${reg.registeredAt}
                                </td>
                            </tr>
                        </c:forEach>
                    </tbody>
                </table>
            </c:otherwise>
        </c:choose>
    </div>
</body>
</html>

