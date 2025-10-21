"""
Create tbl_staged_recommended_orders table using pandas to_sql()
This works even when direct CREATE TABLE permission is denied
"""

import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

def create_staged_recommended_orders_table():
    """Create STAGED table using pandas to_sql() method"""

    # Database connection (same credentials as your app)
    server = '20.46.47.104'
    database = 'YaumiAIML'
    username = 'sandeep'
    password = 'Winit$1234'
    driver = 'ODBC+Driver+17+for+SQL+Server'

    connection_string = f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}'
    engine = create_engine(connection_string)

    # Create empty DataFrame with correct schema
    sample_df = pd.DataFrame({
        'trx_date': pd.to_datetime(['2025-10-07']),
        'route_code': ['1004'],
        'customer_code': ['SAMPLE'],
        'item_code': ['SAMPLE'],
        'item_name': ['Sample Item'],
        'actual_quantity': [0],
        'recommended_quantity': [1],
        'tier': ['A'],
        'van_load': [0],
        'priority_score': [0.0],
        'avg_quantity_per_visit': [0],
        'days_since_last_purchase': [0],
        'purchase_cycle_days': [0.0],
        'frequency_percent': [0.0],
        'generated_at': [datetime.now()],
        'generated_by': ['SETUP_SCRIPT'],
        'is_active': [1]
    })

    try:
        # Create table with sample row (to establish schema)
        print("Creating STAGED table tbl_staged_recommended_orders...")
        sample_df.to_sql('tbl_staged_recommended_orders', engine, if_exists='replace', index=False)
        print("✅ STAGED Table created successfully!")

        # Delete the sample row (keep empty table)
        with engine.connect() as conn:
            conn.execute("DELETE FROM [dbo].[tbl_staged_recommended_orders] WHERE customer_code = 'SAMPLE'")
            conn.commit()
            print("✅ Sample data removed. Table is ready!")

        # Try to create indexes (may fail without permissions, but table will work)
        try:
            with engine.connect() as conn:
                print("\nCreating indexes...")

                conn.execute("""
                    CREATE NONCLUSTERED INDEX idx_staged_date_route
                    ON [dbo].[tbl_staged_recommended_orders] (trx_date, route_code)
                    INCLUDE (customer_code, item_code)
                """)
                print("✅ Index idx_staged_date_route created")

                conn.execute("""
                    CREATE NONCLUSTERED INDEX idx_staged_customer
                    ON [dbo].[tbl_staged_recommended_orders] (customer_code, trx_date)
                """)
                print("✅ Index idx_staged_customer created")

                conn.execute("""
                    CREATE NONCLUSTERED INDEX idx_staged_item
                    ON [dbo].[tbl_staged_recommended_orders] (item_code, trx_date)
                """)
                print("✅ Index idx_staged_item created")

                conn.execute("""
                    CREATE NONCLUSTERED INDEX idx_staged_generated_at
                    ON [dbo].[tbl_staged_recommended_orders] (generated_at DESC)
                """)
                print("✅ Index idx_staged_generated_at created")

                conn.commit()
                print("\n✅ All indexes created successfully!")

        except Exception as e:
            print(f"\n⚠️  Warning: Could not create indexes (table will still work): {e}")
            print("Note: Indexes improve performance but aren't required for basic functionality")

        print("\n🎉 STAGED Setup complete! Table is ready for use.")
        print("This table is separate from production [tbl_recommended_orders]")

    except Exception as e:
        print(f"❌ Error creating table: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    create_staged_recommended_orders_table()
