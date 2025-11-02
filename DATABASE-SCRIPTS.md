# Database Management Scripts

## Overview

The database has been changed from **in-memory (non-persistent)** to **file-based (persistent)**. This means:

✅ **Data survives server restarts**  
✅ **Database stored in `./data/` folder**  
✅ **Can be backed up and restored**  
✅ **Reset to clean state when needed**

---

## Database Configuration

### **Old Configuration (In-Memory)**
```properties
spring.datasource.url=jdbc:h2:mem:jspdemo
spring.jpa.hibernate.ddl-auto=create-drop
```
- Data deleted on every restart
- Perfect for testing

### **New Configuration (File-Based)**
```properties
spring.datasource.url=jdbc:h2:file:./data/jspdemo
spring.jpa.hibernate.ddl-auto=update
```
- Data persists between restarts
- Database files stored in `./data/` folder
- Schema updated automatically (no data loss)

---

## Reset Database Scripts

Three scripts provided for different environments:

### **1. Windows Batch Script** (Recommended for Windows)

```bash
reset-database.bat
```

**Features:**
- Interactive confirmation
- Stops Java server automatically
- Deletes all database files
- Clear status messages
- Pauses for review

**Usage:**
1. Double-click `reset-database.bat`
2. Press Enter to confirm
3. Script stops server and deletes data
4. Restart server manually

---

### **2. PowerShell Script** (Advanced Windows)

```powershell
.\reset-database.ps1
```

**Features:**
- Requires typing "YES" to confirm (safer)
- Color-coded output
- Better error handling
- More detailed feedback

**Usage:**
```powershell
# Run in PowerShell
.\reset-database.ps1

# Type YES when prompted
```

**Note:** You may need to allow script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### **3. Bash Script** (Linux/Mac/Git Bash)

```bash
./reset-database.sh
```

**Features:**
- Works on Linux, Mac, Git Bash
- Uses `pkill` to stop server
- Unix-style path handling

**Usage:**
```bash
# Make executable (first time only)
chmod +x reset-database.sh

# Run script
./reset-database.sh
```

---

## What the Scripts Do

### **Step 1: Stop Server**
- Kills any running Java/Spring Boot processes
- Waits 2 seconds for graceful shutdown
- Ensures database files can be deleted

### **Step 2: Delete Database Files**
The scripts delete these files from the `data/` folder:

- `jspdemo.mv.db` - Main database file
- `jspdemo.trace.db` - Trace/log file (if exists)
- `*.lock.db` - Lock files (if any)

### **Step 3: Confirmation**
- Shows success message
- Database will be recreated on next start
- All tables will be empty with fresh schema

---

## Manual Database Reset

If scripts don't work, you can reset manually:

### **Windows:**
```cmd
# Stop server (Ctrl+C in server terminal)

# Delete database files
del /F /Q data\jspdemo.mv.db
del /F /Q data\jspdemo.trace.db
del /F /Q data\*.lock.db

# Restart server
.\mvnw.cmd spring-boot:run
```

### **Linux/Mac:**
```bash
# Stop server (Ctrl+C in server terminal)

# Delete database files
rm -f data/jspdemo.mv.db
rm -f data/jspdemo.trace.db
rm -f data/*.lock.db

# Restart server
./mvnw spring-boot:run
```

---

## Database File Location

```
JspDemo1/
├── data/                       # Database folder (created automatically)
│   ├── jspdemo.mv.db          # Main database file
│   ├── jspdemo.trace.db       # Debug trace file
│   └── *.lock.db              # Lock files (temporary)
├── reset-database.bat         # Windows batch script
├── reset-database.ps1         # PowerShell script
├── reset-database.sh          # Bash script (Linux/Mac)
└── DATABASE-SCRIPTS.md        # This file
```

**Note:** The `data/` folder is in `.gitignore` and won't be committed to Git.

---

## When to Reset Database

### **Use Cases:**

1. **Clear Test Data**
   - After running automation scripts
   - Remove fake users and orders
   - Start with clean slate

2. **Schema Changes**
   - If you modify entity classes
   - Tables need to be recreated
   - Avoid migration conflicts

3. **Corrupted Data**
   - Database errors or crashes
   - Inconsistent state
   - Quick fix without debugging

4. **Demo Preparation**
   - Clean slate before showing app
   - Remove old test data
   - Professional presentation

5. **Development Reset**
   - Switch branches with schema changes
   - Test fresh user registration
   - Verify empty state behavior

---

## Backup Database (Before Reset)

If you want to save data before resetting:

### **Windows:**
```cmd
# Create backup folder
mkdir backups

# Copy database file with timestamp
copy data\jspdemo.mv.db backups\jspdemo-backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%.mv.db
```

### **Linux/Mac:**
```bash
# Create backup folder
mkdir -p backups

# Copy database file with timestamp
cp data/jspdemo.mv.db backups/jspdemo-backup-$(date +%Y%m%d-%H%M%S).mv.db
```

### **Restore from Backup:**
```cmd
# Stop server first!

# Windows
copy backups\jspdemo-backup-YYYYMMDD.mv.db data\jspdemo.mv.db

# Linux/Mac
cp backups/jspdemo-backup-YYYYMMDD.mv.db data/jspdemo.mv.db

# Restart server
```

---

## Verify Database State

### **After Reset:**

1. **Check files deleted:**
   ```bash
   # Windows
   dir data
   
   # Linux/Mac
   ls -la data/
   ```
   Should show: "File Not Found" or empty folder

2. **Start server:**
   ```bash
   .\mvnw.cmd spring-boot:run
   ```

3. **Check admin pages:**
   - http://localhost:8080/admin/registrations (should be empty)
   - http://localhost:8080/admin/orders (should be empty)

4. **Verify in H2 Console:**
   - http://localhost:8080/h2-console
   - JDBC URL: `jdbc:h2:file:./data/jspdemo`
   - Run: `SELECT COUNT(*) FROM REGISTRATIONS;` (should return 0)

---

## Troubleshooting

### **Problem: "File in use" error**

**Solution:**
```bash
# Make sure server is stopped
taskkill /F /IM java.exe

# Wait a few seconds
timeout /t 5

# Try reset again
```

### **Problem: "Permission denied"**

**Solution:**
- Run script as Administrator (right-click → Run as Administrator)
- Check file permissions on `data/` folder

### **Problem: Database not recreated**

**Solution:**
```bash
# Check application.properties has correct URL
spring.datasource.url=jdbc:h2:file:./data/jspdemo

# Make sure data/ folder exists
mkdir data

# Restart server
```

### **Problem: Script won't run (PowerShell)**

**Solution:**
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run script
.\reset-database.ps1
```

---

## Comparison: In-Memory vs File-Based

| Feature | In-Memory (Old) | File-Based (New) |
|---------|----------------|------------------|
| **Persistence** | ❌ Lost on restart | ✅ Survives restart |
| **Speed** | ⚡ Extremely fast | ⚡ Fast |
| **Size Limit** | RAM only | Disk space |
| **Backup** | ❌ Not possible | ✅ Copy files |
| **Reset** | Just restart | Run script |
| **Use Case** | Testing | Development/Demo |
| **Data Files** | None | `data/*.db` |

---

## Quick Reference

```bash
# Reset database (Windows)
reset-database.bat

# Reset database (PowerShell)
.\reset-database.ps1

# Reset database (Linux/Mac/Git Bash)
./reset-database.sh

# Start server
.\mvnw.cmd spring-boot:run

# View data
http://localhost:8080/admin/registrations
http://localhost:8080/admin/orders

# H2 Console
http://localhost:8080/h2-console
JDBC URL: jdbc:h2:file:./data/jspdemo
Username: sa
Password: (empty)
```

---

## Next Steps

After resetting the database:

1. **Run automation tests:**
   ```bash
   cd ai-tests
   python demo_automation.py
   ```

2. **Manually test forms:**
   - http://localhost:8080/registration
   - http://localhost:8080/workflow

3. **Verify data saved:**
   - http://localhost:8080/admin/registrations
   - http://localhost:8080/admin/orders

4. **Query database:**
   - Use H2 Console at http://localhost:8080/h2-console

---

## Summary

✅ Database is now **persistent** (survives restarts)  
✅ Data stored in `./data/` folder  
✅ **3 reset scripts** provided (Windows, PowerShell, Bash)  
✅ Easy backup and restore  
✅ Clean slate whenever needed  

The persistent database gives you the best of both worlds:
- Data preservation for demos
- Easy reset for testing
- No complex database installation

