import os
import datetime
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = "/Users/mseddik/IdeaProjects/Backend Project I/users.db"
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_sqlite():
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"db_backup_{date_str}.sqlite3")

    # Copy database file
    shutil.copy(DB_PATH, backup_path)
    print(f"[OK] Backup created: {backup_path}")

    # Keep only last 7 backups
    backups = sorted(os.listdir(BACKUP_DIR))
    while len(backups) > 7:
        backup = backups.pop(0)
        os.remove(os.path.join(BACKUP_DIR, backup))
        print(f"[CLEANUP] Removed old backup: {backup}")

    # if len(backups) > 7:
    #     to_delete = backups[0:len(backups)-7]
    #     for file in to_delete:
    #         os.remove(os.path.join(BACKUP_DIR, file))
    #         print(f"[CLEANUP] Removed old backup: {file}")

if __name__ == "__main__":
    backup_sqlite()
