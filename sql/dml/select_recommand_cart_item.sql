SELECT
    id,
    reg_dtm,
    insert_dt,
    raw_json
FROM groobee_dev.recommand_cart_item_raw
ORDER BY insert_dt DESC
LIMIT 10;
