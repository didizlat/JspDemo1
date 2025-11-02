# ✅ Persistent Database Setup Complete

## What Changed

Your database has been upgraded from **in-memory** to **file-based persistent storage**.

### **Before (In-Memory)**
```
❌ Data deleted on every restart
⚡ Super fast (RAM only)
🧪 Perfect for testing only
```

### **After (File-Based Persistent)**
```
✅ Data survives server restarts
✅ Can backup and restore
✅ Reset to clean state when needed
⚡ Still fast (cached in memory)
📁 Stored in ./data/ folder
```

---

## Database Files Created

```
JspDemo1/
└── data/
    └── jspdemo.mv.db  ✅ Created (16 KB)
```

This file contains all your:
- 👥 User registrations
- 📦 Purchase orders
- 📊 All data tables

---

## New Configuration

### **application.properties**
```properties
# OLD: In-memory (deleted on restart)
spring.datasource.url=jdbc:h2:mem:jspdemo
spring.jpa.hibernate.ddl-auto=create-drop

# NEW: File-based (persistent)
spring.datasource.url=jdbc:h2:file:./data/jspdemo
spring.jpa.hibernate.ddl-auto=update
```

### **Key Changes:**
- `mem:` → `file:` (in-memory to file-based)
- `create-drop` → `update` (preserve data, update schema)

---

## Reset Database Scripts

Three scripts provided to reset database to clean state:

### **1. Windows (Double-Click)**
```
reset-database.bat
```
- Easiest to use
- Interactive prompts
- Stops server automatically

### **2. PowerShell (Advanced)**
```powershell
.\reset-database.ps1
```
- Requires typing "YES"
- Color-coded output
- Better error handling

### **3. Bash (Linux/Mac/Git Bash)**
```bash
./reset-database.sh
```
- Works on Unix systems
- Git Bash compatible

---

## How to Use

### **Normal Operation**
```bash
# Start server (data persists)
.\mvnw.cmd spring-boot:run

# Stop server (Ctrl+C)
# Data is SAVED in ./data/jspdemo.mv.db

# Restart server
.\mvnw.cmd spring-boot:run
# Data is LOADED from file
```

### **Reset to Clean State**
```bash
# Option 1: Double-click
reset-database.bat

# Option 2: PowerShell
.\reset-database.ps1

# Option 3: Command line
del /F /Q data\jspdemo.mv.db
.\mvnw.cmd spring-boot:run
```

---

## Verify Persistence

### **Test Data Persistence:**

1. **Register a user:**
   http://localhost:8080/registration
   
2. **Check database:**
   http://localhost:8080/admin/registrations
   
3. **Restart server** (Ctrl+C, then restart)

4. **Check again:**
   http://localhost:8080/admin/registrations
   
   ✅ **User is still there!**

---

## H2 Console Access

### **Connection Settings:**
```
URL:      http://localhost:8080/h2-console

JDBC URL: jdbc:h2:file:./data/jspdemo  ⚠️ Changed!
Username: sa
Password: (empty)
```

**Note:** The JDBC URL changed from `mem:` to `file:` - update your saved connections!

---

## Backup Database

### **Before resetting, backup your data:**

**Windows:**
```cmd
mkdir backups
copy data\jspdemo.mv.db backups\backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%.mv.db
```

**Linux/Mac:**
```bash
mkdir -p backups
cp data/jspdemo.mv.db backups/backup-$(date +%Y%m%d).mv.db
```

### **Restore from backup:**
```cmd
# Stop server first!
copy backups\backup-YYYYMMDD.mv.db data\jspdemo.mv.db
# Restart server
```

---

## Benefits

### **For Development:**
✅ Don't lose data between code changes  
✅ Test with real accumulated data  
✅ Debug with consistent state  

### **For Demos:**
✅ Prepare data in advance  
✅ Same data across presentations  
✅ Professional appearance  

### **For Testing:**
✅ Reset to clean state easily  
✅ Run tests with known data  
✅ Backup test scenarios  

---

## When to Reset

Use `reset-database` scripts when:

1. 🧹 **Clear test data** - Remove fake users/orders
2. 🔄 **Schema changes** - After modifying entities
3. 🐛 **Corrupted data** - Quick fix for errors
4. 🎬 **Demo prep** - Clean slate presentation
5. 🧪 **Test fresh state** - Verify empty behavior

---

## Files Added

```
✅ reset-database.bat          # Windows batch script
✅ reset-database.ps1          # PowerShell script
✅ reset-database.sh           # Bash script
✅ DATABASE-SCRIPTS.md         # Full documentation
✅ PERSISTENT-DATABASE-SETUP.md # This file
```

Updated:
```
📝 application.properties      # File-based DB config
📝 .gitignore                  # Exclude data/ folder
```

---

## Quick Commands

```bash
# Start server
.\mvnw.cmd spring-boot:run

# Reset database (Windows)
reset-database.bat

# Reset database (PowerShell)
.\reset-database.ps1

# View data
http://localhost:8080/admin/registrations
http://localhost:8080/admin/orders

# Database console
http://localhost:8080/h2-console
```

---

## What's Stored

Your `data/jspdemo.mv.db` file contains:

### **REGISTRATIONS Table:**
- ID, First Name, Last Name
- Email, Phone, Birthdate
- Gender, Country
- Interests, Comments
- Newsletter subscription
- Registration timestamp

### **ORDERS Table:**
- ID, Order Number
- Product, Quantity
- Status
- Order timestamp

---

## Next Steps

1. **Run automation to populate data:**
   ```bash
   cd ai-tests
   python demo_automation.py
   ```

2. **Restart server - data persists!**

3. **When ready to clean:**
   ```bash
   reset-database.bat
   ```

4. **Commit changes to Git**

---

## Troubleshooting

### **Can't delete database file?**
- Server is still running
- Run: `taskkill /F /IM java.exe`
- Wait 5 seconds, try again

### **Database not persisting?**
- Check `application.properties` has `file:` not `mem:`
- Verify `data/` folder exists
- Check file permissions

### **Want in-memory back?**
```properties
# Change in application.properties:
spring.datasource.url=jdbc:h2:mem:jspdemo
spring.jpa.hibernate.ddl-auto=create-drop
```

---

## Summary

✅ **Database is now persistent**  
✅ **Data survives restarts**  
✅ **Easy reset with scripts**  
✅ **Backup and restore capable**  
✅ **Best of both worlds**

Your JSP Demo now has production-like persistence with development-friendly reset capabilities! 🎉

