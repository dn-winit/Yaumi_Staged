"""
Clear all data from tbl_recommended_orders table
"""

import pyodbc

def clear_table():
    """Delete all records from tbl_recommended_orders"""

    server = '20.46.47.104'
    database = 'YaumiAIML'
    username = 'sandeep'
    password = 'Winit$1234'

    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Delete all records
        cursor.execute("DELETE FROM [dbo].[tbl_recommended_orders]")
        conn.commit()

        # Check count
        cursor.execute("SELECT COUNT(*) FROM [dbo].[tbl_recommended_orders]")
        count = cursor.fetchone()[0]

        print(f"Table cleared successfully!")
        print(f"Current record count: {count}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    clear_table()
