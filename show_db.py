"""
Utility script to display PostgreSQL tables, schema, and stored records.
Run with: python show_db.py
"""
import os
import sys

# Ensure backend directory is importable
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from app.db.session import engine
    from sqlalchemy import inspect, text

    print("==================================================")
    print("        AIVOA DATABASE INSPECTION TOOL")
    print("==================================================")

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\n[+] Tables in database: {tables}")

    for table_name in tables:
        print(f"\n--- Schema for Table: '{table_name}' ---")
        columns = inspector.get_columns(table_name)
        for col in columns:
            print(f"  * {col['name']:<24} : {str(col['type']):<15}")

        print(f"\n--- Records in '{table_name}' ---")
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT id, complaint_id, product_name, batch_number, customer_name, reported_by, initial_severity, status, created_at FROM {table_name} ORDER BY id DESC LIMIT 10")).fetchall()
            
            if not result:
                print("  (No records found in table)")
            else:
                print(f"  Found {len(result)} recent record(s):")
                header = f"  {'ID':<5} | {'COMPLAINT ID':<18} | {'PRODUCT':<25} | {'BATCH':<12} | {'CUSTOMER':<22} | {'SEVERITY':<10} | {'STATUS'}"
                print("  " + "-" * len(header))
                print(header)
                print("  " + "-" * len(header))
                for row in result:
                    id_val, cid, prod, batch, cust, src, sev, status, created = row
                    prod_str = (prod or '')[:23]
                    cust_str = (cust or '')[:20]
                    print(f"  {id_val:<5} | {cid or '':<18} | {prod_str:<25} | {batch or '':<12} | {cust_str:<22} | {sev or '':<10} | {status or ''}")
                print("  " + "-" * len(header))

    print("\n==================================================")

except Exception as e:
    print("\n[-] Error connecting to database:", str(e))
    print("Ensure PostgreSQL is running and credentials in .env are correct.")
