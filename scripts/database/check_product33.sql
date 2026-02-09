-- 检查产品33(id=17)的尺寸和风格绑定
-- 可用 psql 或 pgAdmin 执行

SELECT id, name, code, category_id, subcategory_id 
FROM products 
WHERE code = '33' OR id = 17;

SELECT id, product_id, size_name, price, is_active 
FROM product_sizes 
WHERE product_id = 17;

SELECT psc.*, sc.name as style_name 
FROM product_style_categories psc 
LEFT JOIN style_category sc ON sc.id = psc.style_category_id 
WHERE psc.product_id = 17;
