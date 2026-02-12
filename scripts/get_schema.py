import duckdb
import pandas as pd

def get_schema():
    try:
        conn = duckdb.connect('data/sales_app.db', read_only=True)
        tables = conn.execute("SHOW TABLES").df()['name'].tolist()
        
        print(f"Database Schema for sales_app.db\n" + "="*30)
        
        for table in tables:
            print(f"\nTABLE: {table}")
            info = conn.execute(f"PRAGMA table_info('{table}')").df()
            print(info[['name', 'type']])
            
            # Check for keys/uniques
            try:
                indexes = conn.execute(f"PRAGMA index_list('{table}')").df()
                if not indexes.empty:
                    print(f"Indexes: {indexes['name'].tolist()}")
            except:
                pass
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_schema()
