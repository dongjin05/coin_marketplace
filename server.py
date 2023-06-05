from flask import Flask, render_template, redirect, url_for, request, session
from pymongo import MongoClient
import secrets

app = Flask(__name__)
client = MongoClient('mongodb+srv://ehdwlsshin:1234@cluster0.c5tc90g.mongodb.net/')  # MongoDB 연결 설정
db = client['coin_market']  # 데이터베이스 선택
users_collection = db['users']  # 사용자 정보 컬렉션 선택

secret_key = secrets.token_hex(16)
app.secret_key = secret_key


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

# 잔고 페이지
@app.route('/balance')
def balance():
    if 'username' in session:
        username = session['username']
        user_data = users_collection.find_one({'username': username})
        if user_data:
            balance = user_data['balance']
            return render_template('balance.html', balance=balance)
        else:
            return "User not found."
    else:
        return redirect(url_for('login'))

@app.route('/add_money', methods=['POST'])
def add_money():
    username = request.form['username']
    amount = float(request.form['amount'])

    user_data = users_collection.find_one({'username': username})
    if user_data:
        current_balance = user_data['balance']
        updated_balance = current_balance + amount

        users_collection.update_one({'username': username}, {'$set': {'balance': updated_balance}})

        return "Money added successfully."
    else:
        return "User not found."

@app.route('/withdraw_money', methods=['POST'])
def withdraw_money():
    username = request.form['username']
    amount = float(request.form['amount'])

    user_data = users_collection.find_one({'username': username})
    if user_data:
        current_balance = user_data['balance']
        if amount <= current_balance:
            updated_balance = current_balance - amount

            users_collection.update_one({'username': username}, {'$set': {'balance': updated_balance}})

            return "Money withdrawn successfully."
        else:
            return "Insufficient balance."
    else:
        return "User not found."


# 마켓 페이지
@app.route('/market')
def market():
    return render_template('market.html')

# 트렌드 페이지
@app.route('/trend')
def trend():
    return render_template('trend.html')

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

if __name__ == '__main__':
    app.run()
