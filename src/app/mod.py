from sqlalchemy import text
from src.app.db.base import engine

with engine.connect() as conn:
    # conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;"))
    # conn.execute(text("UPDATE users SET is_active = 1 WHERE email = 'mseddik@noon.com';"))
    # conn.execute(text("""
    #        ALTER TABLE products
    #        ADD COLUMN updated_by VARCHAR(100) NOT NULL DEFAULT 'system';
    #    """))
    # conn.execute(text("UPDATE products SET updated_by = 'admin' WHERE updated_by = 'system'"))
    # print(conn.execute(text("SELECT * FROM users WHERE email = 'mseddik@noon.com';")).fetchall())
    # print(conn.execute(text("SELECT * FROM products WHERE id = 2;")).fetchall())
    print(conn.execute(text("SELECT * FROM jobs ;")).fetchall())

    # conn.execute(text("ALTER TABLE jobs ADD COLUMN attempts BOOLEAN DEFAULT 0;"))
    # conn.execute(text("ALTER TABLE jobs ADD COLUMN max_attempts BOOLEAN DEFAULT 3;"))
    # conn.execute(text("UPDATE jobs SET status = 'pending' WHERE id = '4';"))
    # conn.execute(text("UPDATE users SET is_active = 0 WHERE email = 'mahmoud.seddik@hotmail.com';"))






    conn.commit()

print("User updated")
