import sqlite3

# 检查当前数据库
conn = sqlite3.connect('pet_painting.db')
cursor = conn.cursor()

# 检查订单数量
cursor.execute('SELECT COUNT(*) FROM "order"')
order_count = cursor.fetchone()[0]
print(f'当前数据库中的订单数量: {order_count}')

# 检查用户数量
cursor.execute('SELECT COUNT(*) FROM user')
user_count = cursor.fetchone()[0]
print(f'当前数据库中的用户数量: {user_count}')

# 检查图片数量
cursor.execute('SELECT COUNT(*) FROM order_image')
image_count = cursor.fetchone()[0]
print(f'当前数据库中的图片数量: {image_count}')

# 显示前几个订单
cursor.execute('SELECT order_number, customer_name, status FROM "order" LIMIT 5')
orders = cursor.fetchall()
print(f'前5个订单: {orders}')

conn.close()

