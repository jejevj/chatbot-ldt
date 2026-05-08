-- Create view for data terbuka
-- This view aggregates data from your source table(s)

-- Option 1: If data is in single table
CREATE OR REPLACE VIEW v_detail_data_terbuka AS
SELECT 
    url,
    kode_data,
    tipe_data,
    kategori_data,
    sifat_data,
    deskripsi_data,
    judul_data
FROM 
    data_terbuka;  -- Replace with your actual table name

-- Option 2: If data is from multiple tables (example with JOIN)
-- CREATE OR REPLACE VIEW v_detail_data_terbuka AS
-- SELECT 
--     d.url,
--     d.kode_data,
--     t.tipe_data,
--     k.kategori_data,
--     d.sifat_data,
--     d.deskripsi_data,
--     d.judul_data
-- FROM 
--     data_master d
--     LEFT JOIN tipe_data t ON d.tipe_id = t.id
--     LEFT JOIN kategori_data k ON d.kategori_id = k.id;

-- Grant permissions
GRANT SELECT ON v_detail_data_terbuka TO PUBLIC;

-- Verify view created
SELECT COUNT(*) as total_records FROM v_detail_data_terbuka;
