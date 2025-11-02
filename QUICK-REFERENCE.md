# Quick Reference Guide

## 🚀 Fast Commands (Recommended)

```batch
# Start server (FAST - ~10 seconds)
quick-start.bat

# After code changes (rebuild + start)
rebuild-and-start.bat

# Stop server (instant)
stop-server.bat

# Reset database
reset-database.bat
```

---

## 🐌 Slow Commands (Old Method)

```batch
# Start server (SLOW - ~30 seconds)
mvnw.cmd spring-boot:run

# Stop server (slow - Ctrl+C)
```

---

## 📊 Database Admin Pages

```
Registrations: http://localhost:8080/admin/registrations
Orders:        http://localhost:8080/admin/orders
H2 Console:    http://localhost:8080/h2-console
```

**H2 Console Login:**
- JDBC URL: `jdbc:h2:file:./data/jspdemo`
- Username: `sa`
- Password: (empty)

---

## 🧪 Testing

```batch
# Run Python automation
cd ai-tests
python quick_test.py

# View results
http://localhost:8080/admin/registrations
http://localhost:8080/admin/orders
```

---

## 🔧 Maintenance

```batch
# Reset database to clean state
reset-database.bat

# Rebuild JAR
mvnw.cmd clean package -DskipTests

# Run tests
mvnw.cmd test
```

---

## 📝 Git Commands

```batch
# Status
git status

# Add all
git add .

# Commit
git commit -m "Your message"

# View history
git log --oneline
```

---

## ⚡ Speed Comparison

| Task | Old Method | New Method | Time Saved |
|------|-----------|------------|------------|
| Start | 30s | 10s | 20s (2-3x faster) |
| Stop | 5s | Instant | 5s |
| Restart | 35s | 10s | 25s (3.5x faster) |

---

## 🎯 Daily Workflow

**Morning:**
```batch
quick-start.bat
```

**After code changes:**
```batch
Ctrl+C
rebuild-and-start.bat
```

**Testing:**
```batch
cd ai-tests
python quick_test.py
```

**End of day:**
```batch
stop-server.bat
```

---

## 📱 Main App URLs

```
Homepage:      http://localhost:8080/
Registration:  http://localhost:8080/registration
Workflow:      http://localhost:8080/workflow
Login:         http://localhost:8080/login
```

---

## 🆘 Troubleshooting

**Port 8080 in use:**
```batch
netstat -ano | findstr :8080
taskkill /PID <pid> /F
```

**Database locked:**
```batch
stop-server.bat
timeout /t 5
reset-database.bat
```

**JAR not found:**
```batch
rebuild-and-start.bat
```

---

## 📚 Documentation

- `README.md` - Project overview
- `TESTING.md` - Testing guide  
- `DATABASE-GUIDE.md` - Database details
- `DATABASE-SCRIPTS.md` - Reset scripts
- `FAST-STARTUP-GUIDE.md` - Speed optimization
- `SETUP-COMPLETE.md` - Full setup guide

---

## 🎓 Learning Resources

**Spring Boot:**
- Auto-configuration
- Embedded Tomcat
- JPA/Hibernate
- H2 Database

**Testing:**
- Playwright (Python & TypeScript)
- Faker for test data
- Browser automation

**Architecture:**
- MVC pattern
- POST-Redirect-GET
- Repository pattern
- Entity mapping

---

## 🔑 Key Files

```
quick-start.bat              - Fast server start
rebuild-and-start.bat        - Rebuild + start
stop-server.bat              - Stop server
reset-database.bat           - Reset database

data/jspdemo.mv.db           - Database file
application.properties       - Configuration
pom.xml                      - Maven config

ai-tests/quick_test.py       - Python automation
ui-tests/playwright.config.ts - TypeScript config
```

---

## ⚙️ Configuration

**application.properties:**
```properties
server.port=8080
spring.datasource.url=jdbc:h2:file:./data/jspdemo
spring.jpa.hibernate.ddl-auto=update
```

**Change port:**
```properties
server.port=9090
```

**Switch to in-memory DB (for testing):**
```properties
spring.datasource.url=jdbc:h2:mem:jspdemo
spring.jpa.hibernate.ddl-auto=create-drop
```

---

## 🎉 Quick Start Checklist

- [ ] Server running: `quick-start.bat`
- [ ] Homepage loads: http://localhost:8080
- [ ] Can register user: http://localhost:8080/registration
- [ ] Can create order: http://localhost:8080/workflow
- [ ] Database persists: restart server, check admin pages
- [ ] Can reset: `reset-database.bat`

---

**Keep this guide handy for quick reference!** 📌

