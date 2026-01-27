-- 创建商城相关数据表
-- 执行此SQL脚本以创建商城功能所需的数据表

-- 商城产品表
CREATE TABLE IF NOT EXISTS shop_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 商城产品图片表
CREATE TABLE IF NOT EXISTS shop_product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES shop_products(id) ON DELETE CASCADE
);

-- 商城产品规格表
CREATE TABLE IF NOT EXISTS shop_product_sizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    size_name VARCHAR(100) NOT NULL,
    price REAL NOT NULL,
    stock INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES shop_products(id) ON DELETE CASCADE
);

-- 商城订单表
CREATE TABLE IF NOT EXISTS shop_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    original_order_id INTEGER,
    original_order_number VARCHAR(50),
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    openid VARCHAR(100),
    customer_address TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    size_id INTEGER NOT NULL,
    size_name VARCHAR(100) NOT NULL,
    image_url VARCHAR(500),
    quantity INTEGER DEFAULT 1 NOT NULL,
    price REAL NOT NULL,
    total_price REAL NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    logistics_info TEXT,
    shipping_time DATETIME,
    payment_time DATETIME,
    transaction_id VARCHAR(100),
    customer_note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (original_order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES shop_products(id),
    FOREIGN KEY (size_id) REFERENCES shop_product_sizes(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_shop_products_code ON shop_products(code);
CREATE INDEX IF NOT EXISTS idx_shop_products_active ON shop_products(is_active);
CREATE INDEX IF NOT EXISTS idx_shop_product_images_product ON shop_product_images(product_id);
CREATE INDEX IF NOT EXISTS idx_shop_product_sizes_product ON shop_product_sizes(product_id);
CREATE INDEX IF NOT EXISTS idx_shop_orders_number ON shop_orders(order_number);
CREATE INDEX IF NOT EXISTS idx_shop_orders_openid ON shop_orders(openid);
CREATE INDEX IF NOT EXISTS idx_shop_orders_original ON shop_orders(original_order_id);
CREATE INDEX IF NOT EXISTS idx_shop_orders_status ON shop_orders(status);
