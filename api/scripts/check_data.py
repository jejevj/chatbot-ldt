"""
Script untuk cek data di view v_detail_data_terbuka
"""
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

password = quote_plus("qwert12345!")
DATABASE_URL = f"postgresql://postgres:{password}@127.0.0.1:5433/satu_data_db"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check total rows
    result = conn.execute(text("SELECT COUNT(*) FROM v_detail_data_terbuka"))
    total = result.scalar()
    print(f"Total rows in view: {total}")
    
    # Check for NULL urls
    result = conn.execute(text("SELECT COUNT(*) FROM v_detail_data_terbuka WHERE url IS NULL"))
    null_urls = result.scalar()
    print(f"Rows with NULL url: {null_urls}")
    
    # Check for duplicate urls
    result = conn.execute(text("""
        SELECT url, COUNT(*) as cnt 
        FROM v_detail_data_terbuka 
        WHERE url IS NOT NULL
        GROUP BY url 
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    print(f"Duplicate URLs: {len(duplicates)}")
    if duplicates:
        for dup in duplicates[:5]:
            print(f"  - {dup[0]}: {dup[1]} times")
    
    # Check unique urls
    result = conn.execute(text("SELECT COUNT(DISTINCT url) FROM v_detail_data_terbuka WHERE url IS NOT NULL"))
    unique_urls = result.scalar()
    print(f"Unique non-NULL URLs: {unique_urls}")
    
    # Show sample data
    print("\nSample data:")
    result = conn.execute(text("SELECT url, kode_data, judul_data FROM v_detail_data_terbuka LIMIT 5"))
    for row in result:
        print(f"  - URL: {row[0][:50] if row[0] else 'NULL'}... | Kode: {row[1]} | Judul: {row[2]}")
