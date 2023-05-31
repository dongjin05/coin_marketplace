from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

# 메인 페이지
@app.route('/')
def main():
    return render_template('main.html')

# 로그인 페이지
@app.route('/login')
def login():
    return render_template('login.html')

# 회원 가입 페이지
@app.route('/signup')
def signup():
    return render_template('signup.html')

# 잔고 페이지
@app.route('/balance')
def balance():
    return render_template('balance.html')

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
