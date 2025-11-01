<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/fmt" prefix="fmt" %>
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Orders</title>
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
            max-width: 1200px;
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
        .product-cell {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .product-icon {
            font-size: 1.5em;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
            background: #d4edda;
            color: #155724;
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
        console.log('Admin orders page loaded');
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
        
        <h1>Orders Database</h1>
        <p class="subtitle">View all completed orders</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">${orders.size()}</div>
                <div class="stat-label">Total Orders</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">
                    <c:set var="totalItems" value="0"/>
                    <c:forEach var="order" items="${orders}">
                        <c:set var="totalItems" value="${totalItems + order.quantity}"/>
                    </c:forEach>
                    ${totalItems}
                </div>
                <div class="stat-label">Total Items Ordered</div>
            </div>
        </div>
        
        <c:choose>
            <c:when test="${empty orders}">
                <div class="empty-state">
                    <div class="empty-state-icon">📦</div>
                    <h2>No Orders Yet</h2>
                    <p>Go to <a href="/workflow" style="color: #667eea;">Workflow Demo</a> to create test orders</p>
                </div>
            </c:when>
            <c:otherwise>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Order #</th>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Status</th>
                            <th>Order Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        <c:forEach var="order" items="${orders}">
                            <tr>
                                <td>#${order.id}</td>
                                <td><strong>${order.orderNumber}</strong></td>
                                <td>
                                    <div class="product-cell">
                                        <span class="product-icon">
                                            <c:choose>
                                                <c:when test="${order.product == 'laptop'}">💻</c:when>
                                                <c:when test="${order.product == 'phone'}">📱</c:when>
                                                <c:when test="${order.product == 'tablet'}">📟</c:when>
                                                <c:when test="${order.product == 'watch'}">⌚</c:when>
                                                <c:otherwise>📦</c:otherwise>
                                            </c:choose>
                                        </span>
                                        <span style="text-transform: capitalize;">${order.product}</span>
                                    </div>
                                </td>
                                <td><strong>${order.quantity}</strong></td>
                                <td><span class="badge">${order.status}</span></td>
                                <td style="font-size: 0.85em;">
                                    <fmt:formatDate value="${order.orderedAt}" pattern="yyyy-MM-dd HH:mm:ss"/>
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

