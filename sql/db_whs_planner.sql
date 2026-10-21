-- =====================================================================
-- Warehouse Capacity Planner - DDL & Seed Data
-- Database : db_whs_planner
-- Target   : MySQL 8.0.16+ (CHECK constraint baru ditegakkan mulai versi ini)
-- Naming   : snake_case konsisten untuk semua tabel & kolom
-- =====================================================================

CREATE DATABASE IF NOT EXISTS db_whs_planner
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE db_whs_planner;

-- ---------------------------------------------------------------------
-- (Opsional) Reset total untuk environment development.
-- Urutan drop: child dulu, baru parent.
-- ---------------------------------------------------------------------
-- DROP TABLE IF EXISTS inbound_detail;
-- DROP TABLE IF EXISTS inbound_history;
-- DROP TABLE IF EXISTS master_sku;

-- ---------------------------------------------------------------------
-- 1. master_sku
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS master_sku (
    item_id     VARCHAR(50)  NOT NULL,
    description VARCHAR(255) NOT NULL,
    cpp         INT          NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                             ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_master_sku PRIMARY KEY (item_id),
    CONSTRAINT chk_master_sku_cpp CHECK (cpp > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. inbound_history
--    (kolom total_line sengaja TIDAK ada; hitung via COUNT() di backend)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inbound_history (
    history_id             INT          NOT NULL AUTO_INCREMENT,
    file_name              VARCHAR(255) NOT NULL,
    total_container        INT          NOT NULL DEFAULT 0,
    total_qty_cs           INT          NOT NULL DEFAULT 0,
    total_required_pallets INT          NOT NULL DEFAULT 0,
    status                 VARCHAR(20)  NOT NULL,
    upload_time            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_inbound_history PRIMARY KEY (history_id),
    CONSTRAINT chk_inbound_history_status
        CHECK (status IN ('Success', 'Failed')),
    CONSTRAINT chk_inbound_history_totals
        CHECK (total_container >= 0 AND total_qty_cs >= 0 AND total_required_pallets >= 0),
    INDEX idx_inbound_history_upload_time (upload_time),
    INDEX idx_inbound_history_status (status, upload_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. inbound_detail
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inbound_detail (
    detail_id        INT         NOT NULL AUTO_INCREMENT,
    history_id       INT         NOT NULL,
    container_number VARCHAR(50) NOT NULL,
    batch_number     VARCHAR(50) NOT NULL,
    item_id          VARCHAR(50) NOT NULL,
    qty_carton       INT         NOT NULL,
    qty_pallet       INT         NOT NULL,
    CONSTRAINT pk_inbound_detail PRIMARY KEY (detail_id),
    CONSTRAINT fk_inbound_detail_history
        FOREIGN KEY (history_id) REFERENCES inbound_history (history_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_inbound_detail_item
        FOREIGN KEY (item_id) REFERENCES master_sku (item_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_inbound_detail_qty
        CHECK (qty_carton > 0 AND qty_pallet > 0),
    -- Aturan bisnis: 1 baris per kombinasi Container + SKU + Batch per upload
    CONSTRAINT uq_inbound_detail_combo
        UNIQUE (history_id, container_number, batch_number, item_id),
    INDEX idx_inbound_detail_history (history_id),
    INDEX idx_inbound_detail_item (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Seed data: 10 sampel master_sku (dari mockup UI + ITEM013 dari sample
-- inbound plan, supaya file INB_PLAN bisa langsung dites)
-- ---------------------------------------------------------------------
INSERT INTO master_sku (item_id, description, cpp) VALUES
    ('ITEM004', '[MATERIAL] SMALL PAPER BAG (50)',            30),
    ('ITEM005', 'MADBURY HOT COCOA POWDER 1 KG X 18 PACK',    48),
    ('ITEM006', 'FRESH MILK PASTEURIZED 995 ML X 12 PACK',    60),
    ('ITEM007', 'MATCHA POWDER 500 GR X 24 PACK',             72),
    ('ITEM008', 'NATURAL HONEY 250 ML X 24 BOTL',             36),
    ('ITEM009', 'CHOCOLATE CUPCAKE MIX 2,5 KG X 4 BAG',       24),
    ('ITEM010', 'COOKIES MIX 2,5 KG X 4 BAG',                 24),
    ('ITEM011', 'DONUT MIX 1 KG X 10 BAG',                    32),
    ('ITEM012', 'PLASTIC CUP 20 Oz 250 PCS X 6 PACK',         48),
    ('ITEM013', 'PAPER STRAW 1000 PCS X 5 PACK',              72);

-- ---------------------------------------------------------------------
-- Referensi query backend (bukan bagian dari skema)
-- ---------------------------------------------------------------------
-- Jumlah baris (Lines) per history, menggantikan kolom total_line:
-- SELECT h.history_id, h.file_name, COUNT(d.detail_id) AS total_line
-- FROM inbound_history h
-- LEFT JOIN inbound_detail d ON d.history_id = h.history_id
-- GROUP BY h.history_id, h.file_name;
--
-- UPSERT master SKU (hindari TRUNCATE/DELETE karena FK RESTRICT):
-- INSERT INTO master_sku (item_id, description, cpp)
-- VALUES (%s, %s, %s)
-- ON DUPLICATE KEY UPDATE description = VALUES(description), cpp = VALUES(cpp);
