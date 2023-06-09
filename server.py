from flask import Flask, render_template, redirect, url_for, request, session
from pymongo import MongoClient
import secrets
import time
import json

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
        coin_data = coins_collection.find_one()

        if user_data and coin_data:
            current_balance = user_data['balance']
            available_coins = user_data.get('coins', 0)
            coin_quantity = coin_data.get('quantity', 0)

            if available_coins >= number_of_coins and coin_quantity >= number_of_coins:
                coins_value = number_of_coins * selling_price
                updated_balance = current_balance + coins_value
                updated_coins = available_coins - number_of_coins
                updated_coin_quantity = coin_quantity - number_of_coins

                # Add the sell order to the queue
                sell_order = {
                    'username': username,
                    'number_of_coins': number_of_coins,
                    'selling_price': selling_price
                }
                queue_collection.insert_one(sell_order)

                
                # Update the coin price
                coins_collection.update_one({}, {'$set': {'price': selling_price}})

                # Update the coin quantity
                coins_collection.update_one({}, {'$set': {'quantity': updated_coin_quantity}})

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


# 코인 구매
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
                    'type': 'Buy',
                    'coins': number_of_coins,
                    'price': coin_price
                }
                users_collection.update_one({'username': username}, {'$push': {'trade_history': trade}})


                time.sleep(1)  # Add a delay of 1 second before redirecting
                return redirect(url_for('market'))
            else:
                return "Insufficient balance."
        else:
            return "User not found."
    else:
        return redirect(url_for('login'))


# 마켓 페이지
@app.route('/market')
def market():
    sell_orders = queue_collection.find().sort('selling_price', 1)
    coin_data = coins_collection.find_one()
    if coin_data:
        initial_coin_quantity = coin_data.get('quantity', 0)
        initial_coin_price = coin_data.get('price', 0)
    else:
        initial_coin_quantity = 0
        initial_coin_price = 0
    return render_template('market.html', initial_coin_quantity=initial_coin_quantity, initial_coin_price=initial_coin_price, sell_orders=sell_orders)

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

