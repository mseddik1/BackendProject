from sqlalchemy import text
from src.app.db.base import engine

with engine.connect() as conn:
    # conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;"))
    # conn.execute(text("UPDATE users SET is_active = 1 WHERE email = 'mseddik@noon.com';"))
    # conn.execute(text("""
    #        ALTER TABLE products
    #        ADD COLUMN updated_by VARCHAR(100) NOT NULL DEFAULT 'system';
    #    """))
    conn.execute(text("UPDATE products SET updated_by = 'admin' WHERE updated_by = 'system'"))
    # print(conn.execute(text("SELECT * FROM users WHERE email = 'mseddik@noon.com';")).fetchall())
    print(conn.execute(text("SELECT * FROM products WHERE id = 2;")).fetchall())


    conn.commit()

print("User updated")
