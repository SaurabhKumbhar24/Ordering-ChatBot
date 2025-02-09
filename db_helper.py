import mysql.connector

cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='saurabh',
    database='smt'
)

def get_next_order_id():

    cursor = cnx.cursor()
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)
    
    result = cursor.fetchone()[0]

    cursor.close()

    if result is None:
        return 1
    else:
        return result + 1

def insert_order_item(food_item, quantity, next_order_id):
    
    cursor = cnx.cursor()
    query = "SELECT item_id, price FROM food_items WHERE name = %s;"
    cursor.execute(query,[food_item])
    result = cursor.fetchone()
    item_id, price = result
    total_price = float(price) * float(quantity)

    insert_query = "INSERT INTO orders (order_id, item_id, quantity, total_price) VALUES (%s, %s, %s, %s);"
    cursor.execute(insert_query,[int(next_order_id),int(item_id),int(quantity),int(total_price)])
    
    cursor.close()
    return 1
    

def get_total_order_price(order_id):

    cursor = cnx.cursor()
    query = f"SELECT SUM(total_price) FROM orders WHERE order_id = {order_id};"
    cursor.execute(query)

    result = cursor.fetchone()[0]

    cursor.close()

    return result