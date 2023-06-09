from flask import Flask, render_template, flash, redirect, url_for, request, session
from pymongo import MongoClient
import secrets
import time
from bson.objectid import ObjectId

app = Flask(__name__)
client = MongoClient('mongodb+srv://ehdwlsshin:1234@cluster0.c5tc90g.mongodb.net/')
db = client['coin_market']
users_collection = db['users']
queue_collection = db['queue']
coins_collection = db['coins']  # Coin collection to store the market's coin quantity

secret_key = secrets.token_hex(16)
app.secret_key = secret_key

initial_coin_price = 100
initial_coin_quantity = 100
price_trend = [initial_coin_price]  # 가격 트렌드 데이터 초기화

# Initialize coins collection if it's empty
if coins_collection.count_documents({}) == 0:
    coins_collection.insert_one({'quantity': 100, 'price': 100})


# 메인 페이지
@app.route('/')
def main():
    return render_template('main.html')

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = users_collection.find_one({'username': username})
        if user_data and user_data['password'] == password:
            session['username'] = username
            return redirect(url_for('main'))
        else:
            return "Invalid username or password."

    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('main'))

# 회원 가입 페이지
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        balance = 0
        user_data = {'username': username, 'password': password, 'balance': balance}
        users_collection.insert_one(user_data)
        return render_template('signup.html', success_message=True)
    return render_template('signup.html', success_message=False)

# 거래 기록 페이지
@app.route('/history')
def history():
    if 'username' in session:
        username = session['username']
        user_data = users_collection.find_one({'username': username})
        if user_data:
            trade_history = user_data.get('trade_history', [])
            return render_template('history.html', trade_history=trade_history)
        else:
            return "User not found."
    else:
        return redirect(url_for('login'))

# 잔고 페이지
@app.route('/balance')
def balance():
    if 'username' in session:
        username = session['username']
        user_data = users_collection.find_one({'username': username})
        if user_data:
            balance = user_data['balance']
            coins = user_data.get('coins', 0)  # 보유 중인 코인 개수
            return render_template('balance.html', balance=balance, coins=coins)
        else:
            return "User not found."
    else:
        return redirect(url_for('login'))

# 잔고 추가
@app.route('/add_money', methods=['POST'])
def add_money():
    if 'username' in session:
        username = session['username']
        amount = float(request.form['amount'])
        user_data = users_collection.find_one({'username': username})

        if user_data:
            current_balance = user_data['balance']
            updated_balance = current_balance + amount

            users_collection.update_one({'username': username}, {'$set': {'balance': updated_balance}})
            time.sleep(1)  # Add a delay of 2 seconds before redirecting
            return redirect(url_for('balance'))
        else:
            return "User not found."
    else:
        return redirect(url_for('login'))


# 잔고 인출
@app.route('/withdraw_money', methods=['POST'])
def withdraw_money():
    if 'username' in session:
        username = session['username']
        amount = float(request.form['amount'])
        user_data = users_collection.find_one({'username': username})

        if user_data:
            current_balance = user_data['balance']
            if amount <= current_balance:
                updated_balance = current_balance - amount
                users_collection.update_one({'username': username}, {'$set': {'balance': updated_balance}})
                time.sleep(1)  # Add a delay of 2 seconds before redirecting
                return redirect(url_for('balance'))
            else:
                return "Insufficient balance."
        else:
            return "User not found."
    else:
        return redirect(url_for('login'))
    
# 코인 판매
@app.route('/sell_coins', methods=['POST'])
def sell_coins():
    if 'username' in session:
        username = session['username']
        number_of_coins = int(request.form['number_of_coins'])
        selling_price = float(request.form['selling_price'])
        user_data = users_collection.find_one({'username': username})

        if user_data:
            coins_available = user_data.get('coins', 0)
            if coins_available >= number_of_coins:
                updated_coins = coins_available - number_of_coins

                # Update user's coin balance
                users_collection.update_one({'username': username}, {'$set': {'coins': updated_coins}})

                # Add the listing to the queue collection
                sell_order = {
                    'seller': username,
                    'quantity': number_of_coins,
                    'price': selling_price
                }
                queue_collection.insert_one(sell_order)

                # Add trade history
                trade = {
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'Sell',
                    'coins': number_of_coins,
                    'price': selling_price
                }
                users_collection.update_one({'username': username}, {'$push': {'trade_history': trade}})

                time.sleep(1)  # Add a delay of 1 second before redirecting
                return redirect(url_for('market'))
            else:
                return "Insufficient coins."
        else:
            return "User not found."
    else:
        return redirect(url_for('login'))
    

# 코인 구매(마켓)
@app.route('/buy_coins', methods=['POST'])
def buy_coins():
    if 'username' in session:
        username = session['username']
        number_of_coins = int(request.form['number_of_coins'])
        user_data = users_collection.find_one({'username': username})

        if user_data:
            current_balance = user_data['balance']
            coin_price = initial_coin_price
            required_amount = number_of_coins * coin_price

            if current_balance >= required_amount:
                updated_balance = current_balance - required_amount
                updated_coins = user_data.get('coins', 0) + number_of_coins

                users_collection.update_one(
                    {'username': username},
                    {'$set': {'balance': updated_balance, 'coins': updated_coins}}
                )

                # Add trade history
                trade = {
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'Buy from market',
                    'coins': number_of_coins,
                    'price': coin_price
                }
                users_collection.update_one({'username': username}, {'$push': {'trade_history': trade}})

                # Reduce coin quantity in the market
                coin_data = coins_collection.find_one()
                if coin_data:
                    initial_coin_quantity = coin_data.get('quantity', 0)
                    if initial_coin_quantity >= number_of_coins:
                        updated_coin_quantity = initial_coin_quantity - number_of_coins
                        coins_collection.update_one({}, {'$set': {'quantity': updated_coin_quantity}})
                    else:
                        flash("Insufficient coins in the market!", "error")
                else:
                    flash("Coin data not found in the market!", "error")

                flash(f"You have successfully bought {number_of_coins} coins from the market!", "success")
                time.sleep(1)  # Add a delay of 1 second before redirecting
                return redirect(url_for('market'))
            else:
                return "Insufficient balance."
        else:
            return "User not found."
    else:
        return redirect(url_for('login'))

# 코인 구매(유저)
@app.route('/buy_order', methods=['POST'])
def buy_order():
    order_id = request.form.get('order_id')
    sell_order = queue_collection.find_one({'_id': ObjectId(order_id)})
    if sell_order:
        # Process the purchase based on the sell_order
        # For example, deduct coins from the buyer and update seller's balance
        buyer_username = session['username']
        buyer_data = users_collection.find_one({'username': buyer_username})
        seller_username = sell_order['seller']
        seller_data = users_collection.find_one({'username': seller_username})

        if buyer_data and seller_data:
            coins_to_buy = sell_order['quantity']
            buying_price = sell_order['price']
            buyer_coins = buyer_data.get('coins', 0)
            buyer_balance = buyer_data.get('balance', 0)
            seller_balance = seller_data.get('balance', 0)

            # Calculate the total cost for the buyer
            total_cost = coins_to_buy * buying_price

            if buyer_balance >= total_cost:
                # Deduct coins from the buyer
                new_buyer_balance = buyer_balance - total_cost
                users_collection.update_one({'username': buyer_username}, {'$set': {'balance': new_buyer_balance}})

                # Add coins to the seller
                new_buyer_coins = buyer_coins + coins_to_buy
                users_collection.update_one({'username': buyer_username}, {'$set': {'coins': new_buyer_coins}})

                new_seller_balance = seller_balance + total_cost
                users_collection.update_one({'username': seller_username}, {'$set': {'balance': new_seller_balance}})

                # Remove the sell order from the queue
                queue_collection.delete_one({'_id': ObjectId(order_id)})
                
                trade = {
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'Buy',
                    'coins': coins_to_buy,
                    'price': buying_price
                }
                users_collection.update_one({'username': buyer_username}, {'$push': {'trade_history': trade}})

                # Redirect the user to the market page after the successful purchase
                return redirect('/market')

    # If the sell_order doesn't exist or the purchase couldn't be processed, handle the error
    return "Error: Unable to process the purchase"

# 마켓 페이지
@app.route('/market')
def market():
    coins = 0  # Set a default value for coins
    if 'username' in session:
        username = session['username']
        user_data = users_collection.find_one({'username': username})
        if user_data:
            coins = user_data.get('coins', 0)  # Update the value of coins if user_data exists
    sell_orders = queue_collection.find().sort('price', 1)
    coin_data = coins_collection.find_one()
    if coin_data:
        initial_coin_quantity = coin_data.get('quantity', 0)
        initial_coin_price = coin_data.get('price', 0)
    else:
        initial_coin_quantity = 0
        initial_coin_price = 0
    return render_template('market.html', initial_coin_quantity=initial_coin_quantity, initial_coin_price=initial_coin_price, sell_orders=sell_orders, user_coin_balance=coins)

# 트렌드 페이지
@app.route('/trend')
def trend():
    return render_template('trend.html', available_coins=initial_coin_quantity, coin_price=initial_coin_price, price_trend=price_trend)

# 코인 가격 업데이트
def update_coin_price(new_price):
    price_trend.append(new_price)

# 메인 페이지로 이동하는 버튼
@app.route('/go_main')
def go_main():
    return redirect(url_for('main'))

# 로그인 페이지로 이동하는 버튼
@app.route('/go_login')
def go_login():
    return redirect(url_for('login'))

# 회원 가입 페이지로 이동하는 버튼
@app.route('/go_signup')
def go_signup():
    return redirect(url_for('signup'))

# 잔고 페이지로 이동하는 버튼
@app.route('/go_balance')
def go_balance():
    return redirect(url_for('balance'))

# 마켓 페이지로 이동하는 버튼
@app.route('/go_market')
def go_market():
    return redirect(url_for('market'))

# 트렌드 페이지로 이동하는 버튼
@app.route('/go_trend')
def go_trend():
    return redirect(url_for('trend'))

# 거래 기록 페이지로 이동하는 버튼
@app.route('/go_history')
def go_history():
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True)
