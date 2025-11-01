from flask import Flask, render_template
from flask_cors import CORS
from auth import auth_bp, init_user_db
from chatbox import app as chatbot_app  # import app có route /ask

app = chatbot_app  # Dùng chung Flask app từ chatbox
CORS(app)

# Đăng ký blueprint auth
app.register_blueprint(auth_bp, url_prefix="/auth")

# Tạo database nếu chưa có
init_user_db()

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login')
def form_login():
    return render_template('login.html')

@app.route('/signup')
def form_signup():
    return render_template('signup.html')

@app.route('/forgot')
def form_forgot():
    return render_template('forgot.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/restaurant')
def restaurant_page():
    return render_template('restaurant.html')

@app.route('/restaurant/<dish>')
def restaurant_detail(dish):
    import json
    with open('foods.json', encoding='utf-8') as f:
        data = json.load(f)

    selected = next((item for item in data if item["dish"].lower() == dish.lower()), None)

    if not selected:
        return render_template('restaurant.html', error="Restaurant not found.")

    return render_template('restaurant.html', restaurant=selected)

if __name__ == "__main__":
    print("🚀 Server chạy tại http://127.0.0.1:5000")
    app.run(debug=True)
