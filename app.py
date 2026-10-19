from flask import Flask, render_template, request, redirect, session, url_for, abort
from pathlib import Path
import sqlite3, json, secrets
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # demo only: sessions reset when server restarts
DB = Path(__file__).with_name('orders.db')
PRODUCTS = [{'id':1,'name':'ماتشا كوتارو الأصلية','price':89,'emoji':'🍵'},{'id':2,'name':'كوب كوتارو','price':45,'emoji':'🥤'},{'id':3,'name':'مجموعة الماتشا','price':119,'emoji':'🎁'}]
def init_db():
    with sqlite3.connect(DB) as db:
        db.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, items TEXT, total INTEGER, customer TEXT)')
def cart_data():
    ids=session.get('cart',[])
    items=[dict(p, quantity=ids.count(p['id']), subtotal=ids.count(p['id'])*p['price']) for p in PRODUCTS if p['id'] in ids]
    return items,sum(x['subtotal'] for x in items),len(ids)
@app.context_processor
def shared():
    return {'cart_count':len(session.get('cart',[]))}
@app.get('/')
def home():
    return render_template('index.html',products=PRODUCTS)
@app.post('/add/<int:product_id>')
def add(product_id):
    if not any(p['id']==product_id for p in PRODUCTS):abort(404)
    cart=session.get('cart',[]);cart.append(product_id);session['cart']=cart
    return redirect(url_for('cart'))
@app.get('/cart')
def cart():
    items,total,count=cart_data()
    return render_template('cart.html',items=items,total=total,count=count)
@app.post('/remove/<int:product_id>')
def remove(product_id):
    cart=session.get('cart',[])
    if product_id in cart:cart.remove(product_id);session['cart']=cart
    return redirect(url_for('cart'))
@app.get('/checkout')
def checkout_page():
    items,total,count=cart_data()
    if not count:return redirect(url_for('cart'))
    return render_template('checkout.html',items=items,total=total)
@app.post('/checkout')
def checkout():
    items,total,count=cart_data()
    customer=request.form.get('customer','').strip()
    if not count:return redirect(url_for('cart'))
    if not customer:return render_template('checkout.html',items=items,total=total,error='اكتب الاسم لإكمال الطلب.'),400
    with sqlite3.connect(DB) as db:
        cursor=db.execute('INSERT INTO orders (items,total,customer) VALUES (?,?,?)',(json.dumps(items,ensure_ascii=False),total,customer))
        order_id=cursor.lastrowid
    session['cart']=[]
    return render_template('success.html',order_id=order_id,customer=customer,total=total)
@app.get('/rights')
def rights():
    return render_template('rights.html')
if __name__=='__main__':
    init_db()
    app.run(debug=True)
