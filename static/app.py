from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, static_folder='.', static_url_path='/static', template_folder='.')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login logic here
        email = request.form.get('email')
        password = request.form.get('password')
        # For now, redirect to dashboard after login
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Handle signin logic here
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        # For now, redirect to dashboard after signin
        return redirect(url_for('dashboard'))
    return render_template('signin.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
