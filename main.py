from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_dongguk():
   return 'Hello Dongguk University Students!'

if __name__ == '__main__':
   app.run()
