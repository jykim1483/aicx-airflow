CREATE TABLE IF NOT EXISTS groobee_dev.recommand_cart_item_raw
(
    id String,
    reg_dtm Nullable(DateTime64(3)),
    raw_json String,
    insert_dt DateTime64(3) DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(insert_dt)
PARTITION BY toYYYYMM(ifNull(reg_dtm, insert_dt))
ORDER BY id;