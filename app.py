"""
TN GOVT SCHEME BOT - Main Flask Application
A modern AI-powered web application for helping citizens discover Tamil Nadu government welfare schemes
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
import MySQLdb.cursors
import openai
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from flask_session import Session
import re

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True

Session(app)

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'tn_scheme_bot')
DB_SSL = os.getenv('DB_SSL', 'false').lower() == 'true'

# OpenAI Configuration
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-api-key')

# ============================================
# DATABASE HELPER FUNCTIONS
# ============================================

def get_db_connection():
    """Get database connection"""
    try:
        kwargs = {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'database': DB_NAME,
            'charset': 'utf8mb4',
            'cursorclass': MySQLdb.cursors.DictCursor
        }
        if DB_SSL:
            import ssl
            kwargs['ssl'] = {'cert_reqs': ssl.CERT_NONE}
            
        connection = MySQLdb.connect(**kwargs)
        return connection
    except MySQLdb.Error as e:
        print(f"Database connection error: {e}")
        return None

def query_db(query, args=(), one=False):
    """Execute database query"""
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, args)
        
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall() if not one else cursor.fetchone()
        else:
            conn.commit()
            result = cursor.lastrowid if 'INSERT' in query.upper() else cursor.rowcount
        
        cursor.close()
        conn.close()
        return result
    except MySQLdb.Error as e:
        print(f"Database error: {e}")
        conn.close()
        return None

# ============================================
# AUTHENTICATION DECORATORS
# ============================================

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin access required', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# OPENAI INTEGRATION
# ============================================

def get_scheme_recommendations(user_query, user_profile=None, language='English'):
    """Get scheme recommendations from OpenAI"""
    try:
        # Get available schemes from database
        schemes = query_db("SELECT * FROM schemes WHERE is_active = 1 LIMIT 10")
        schemes_text = json.dumps(schemes, default=str) if schemes else "No schemes available"
        
        # Prepare context for OpenAI
        system_prompt = f"""You are an expert Tamil Nadu government welfare scheme advisor. 
        Your role is to help citizens find the most relevant government schemes based on their profile and queries.
        
        Available schemes database:
        {schemes_text[:2000]}
        
        Always provide:
        1. Recommended schemes with reasons
        2. Eligibility status
        3. Required documents
        4. Application process
        5. Helpful tips
        
        Language: {language}
        {'Respond in Tamil' if language == 'Tamil' else 'Respond in English'}
        """
        
        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "I'm having trouble connecting to the AI system. Please try again later."

def extract_entities(text):
    """Extract entities from user query"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract entities like age, occupation, category from the text in JSON format."},
                {"role": "user", "content": text}
            ],
            temperature=0.5,
            max_tokens=200
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Entity extraction error: {e}")
        return {}

# ============================================
# ROUTES - AUTHENTICATION
# ============================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.form
        
        # Validate input
        if not all([data.get('fullname'), data.get('email'), data.get('password'), data.get('mobile')]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        # Check if email exists
        existing = query_db("SELECT id FROM users WHERE email = %s", (data.get('email'),), one=True)
        if existing:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Hash password
        password_hash = generate_password_hash(data.get('password'))
        
        # Insert user
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash, mobile_number, district, age, gender, occupation, category)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('fullname'),
                data.get('email'),
                password_hash,
                data.get('mobile'),
                data.get('district', 'Unknown'),
                data.get('age', 0),
                data.get('gender', 'Other'),
                data.get('occupation', 'Other'),
                data.get('category', 'General')
            ))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except MySQLdb.Error as e:
            flash(f'Registration error: {str(e)}', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password required', 'danger')
            return redirect(url_for('login'))
        
        # Get user from database
        user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = user['full_name']
            
            # Update last login
            query_db("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password required', 'danger')
            return redirect(url_for('admin_login'))
        
        admin = query_db("SELECT * FROM admins WHERE email = %s", (email,), one=True)
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_email'] = admin['email']
            session['admin_name'] = admin['full_name']
            session['admin_role'] = admin['role']
            
            flash('Admin login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ============================================
# ROUTES - USER DASHBOARD
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user_id = session['user_id']
    
    # Get user data
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    
    # Get recent chats
    chats = query_db("""
        SELECT * FROM chat_history 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 5
    """, (user_id,))
    
    # Get favorite schemes count
    favorites_count = query_db("""
        SELECT COUNT(*) as count FROM favorite_schemes WHERE user_id = %s
    """, (user_id,), one=True)
    
    return render_template('dashboard.html', user=user, chats=chats, favorites_count=favorites_count)

@app.route('/chat')
@login_required
def chat():
    """Chat interface"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """Handle chat requests"""
    data = request.json
    user_query = data.get('message', '')
    language = data.get('language', 'English')
    user_id = session['user_id']
    
    if not user_query:
        return jsonify({'error': 'Empty message'}), 400
    
    # Get AI response
    bot_response = get_scheme_recommendations(user_query, language=language)
    
    # Extract entities
    entities = extract_entities(user_query)
    
    # Save to chat history
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_history (user_id, user_query, bot_response, language, entities)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, user_query, bot_response, language, json.dumps(entities)))
        conn.commit()
        cursor.close()
        conn.close()
    except MySQLdb.Error as e:
        print(f"Error saving chat: {e}")
    
    return jsonify({
        'response': bot_response,
        'entities': entities,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/schemes')
@login_required
def schemes():
    """Browse schemes"""
    category = request.args.get('category', '')
    
    if category:
        schemes_list = query_db("""
            SELECT * FROM schemes WHERE is_active = 1 AND category = %s
        """, (category,))
    else:
        schemes_list = query_db("SELECT * FROM schemes WHERE is_active = 1")
    
    categories = query_db("SELECT DISTINCT category FROM schemes WHERE is_active = 1")
    
    return render_template('schemes.html', schemes=schemes_list, categories=categories)

@app.route('/scheme/<int:scheme_id>')
@login_required
def scheme_detail(scheme_id):
    """Scheme details"""
    scheme = query_db("SELECT * FROM schemes WHERE id = %s", (scheme_id,), one=True)
    
    if not scheme:
        flash('Scheme not found', 'danger')
        return redirect(url_for('schemes'))
    
    return render_template('scheme_detail.html', scheme=scheme)

@app.route('/api/favorite/<int:scheme_id>', methods=['POST'])
@login_required
def toggle_favorite(scheme_id):
    """Toggle favorite scheme"""
    user_id = session['user_id']
    
    # Check if already favorited
    existing = query_db("""
        SELECT id FROM favorite_schemes WHERE user_id = %s AND scheme_id = %s
    """, (user_id, scheme_id), one=True)
    
    if existing:
        query_db("DELETE FROM favorite_schemes WHERE user_id = %s AND scheme_id = %s", (user_id, scheme_id))
        return jsonify({'status': 'removed'})
    else:
        query_db("""
            INSERT INTO favorite_schemes (user_id, scheme_id) VALUES (%s, %s)
        """, (user_id, scheme_id))
        return jsonify({'status': 'added'})

@app.route('/favorites')
@login_required
def favorites():
    """Favorite schemes"""
    user_id = session['user_id']
    
    favorites_list = query_db("""
        SELECT s.* FROM schemes s
        JOIN favorite_schemes f ON s.id = f.scheme_id
        WHERE f.user_id = %s
        ORDER BY f.saved_at DESC
    """, (user_id,))
    
    return render_template('favorites.html', schemes=favorites_list)

@app.route('/eligibility-check')
@login_required
def eligibility_check():
    """Eligibility checker"""
    user_id = session['user_id']
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    
    return render_template('eligibility.html', user=user)

@app.route('/api/check-eligibility', methods=['POST'])
@login_required
def api_check_eligibility():
    """Check eligibility for schemes"""
    data = request.json
    user_id = session['user_id']
    
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    
    # Get all schemes
    schemes = query_db("SELECT * FROM schemes WHERE is_active = 1")
    
    eligible = []
    partially_eligible = []
    not_eligible = []
    
    for scheme in schemes:
        # Simple eligibility check (can be enhanced with AI)
        is_eligible = True
        reasons = []
        
        if scheme['age_min'] and user['age'] < scheme['age_min']:
            is_eligible = False
            reasons.append(f"Age requirement: minimum {scheme['age_min']}")
        
        if scheme['age_max'] and user['age'] > scheme['age_max']:
            is_eligible = False
            reasons.append(f"Age requirement: maximum {scheme['age_max']}")
        
        if scheme['gender_specific'] and scheme['gender_specific'] != user['gender']:
            is_eligible = False
            reasons.append(f"Gender specific: {scheme['gender_specific']}")
        
        if is_eligible:
            eligible.append({
                'id': scheme['id'],
                'name': scheme['scheme_name'],
                'benefit': scheme['benefit_amount']
            })
        else:
            not_eligible.append({
                'id': scheme['id'],
                'name': scheme['scheme_name'],
                'reasons': reasons
            })
    
    return jsonify({
        'eligible': eligible,
        'partially_eligible': partially_eligible,
        'not_eligible': not_eligible
    })

@app.route('/feedback')
@login_required
def feedback():
    """Feedback page"""
    return render_template('feedback.html')

@app.route('/api/submit-feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Submit feedback"""
    data = request.json
    user_id = session['user_id']
    
    query_db("""
        INSERT INTO feedback (user_id, rating, feedback_text, is_helpful)
        VALUES (%s, %s, %s, %s)
    """, (user_id, data.get('rating'), data.get('feedback'), data.get('is_helpful')))
    
    return jsonify({'status': 'success'})

@app.route('/profile')
@login_required
def profile():
    """User profile"""
    user_id = session['user_id']
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    
    return render_template('profile.html', user=user)

@app.route('/api/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.form
    user_id = session['user_id']
    
    query_db("""
        UPDATE users SET 
        full_name = %s,
        mobile_number = %s,
        district = %s,
        age = %s,
        gender = %s,
        occupation = %s,
        category = %s,
        annual_income = %s
        WHERE id = %s
    """, (
        data.get('fullname'),
        data.get('mobile'),
        data.get('district'),
        data.get('age'),
        data.get('gender'),
        data.get('occupation'),
        data.get('category'),
        data.get('income'),
        user_id
    ))
    
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

# ============================================
# ROUTES - ADMIN PANEL
# ============================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = query_db("SELECT COUNT(*) as count FROM users", one=True)
    total_schemes = query_db("SELECT COUNT(*) as count FROM schemes WHERE is_active = 1", one=True)
    total_queries = query_db("SELECT COUNT(*) as count FROM chat_history", one=True)
    
    # Get recent chats
    recent_chats = query_db("""
        SELECT ch.*, u.full_name FROM chat_history ch
        JOIN users u ON ch.user_id = u.id
        ORDER BY ch.created_at DESC
        LIMIT 10
    """)
    
    # Get recent feedback
    recent_feedback = query_db("""
        SELECT f.*, u.full_name FROM feedback f
        JOIN users u ON f.user_id = u.id
        ORDER BY f.created_at DESC
        LIMIT 5
    """)
    
    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_schemes=total_schemes,
        total_queries=total_queries,
        recent_chats=recent_chats,
        recent_feedback=recent_feedback
    )

@app.route('/admin/schemes')
@admin_required
def admin_schemes():
    """Manage schemes"""
    schemes_list = query_db("SELECT * FROM schemes ORDER BY created_at DESC")
    
    return render_template('admin/schemes.html', schemes=schemes_list)

@app.route('/admin/scheme/add', methods=['GET', 'POST'])
@admin_required
def admin_add_scheme():
    """Add new scheme"""
    if request.method == 'POST':
        data = request.form
        
        query_db("""
            INSERT INTO schemes (
                scheme_name, scheme_code, category, description, eligibility,
                age_min, age_max, gender_specific, occupation_specific, category_specific,
                income_limit, required_documents, benefits, benefit_amount,
                application_process, district, is_state_wide, official_link,
                application_link, helpline, email, office_address
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            data.get('scheme_name'),
            data.get('scheme_code'),
            data.get('category'),
            data.get('description'),
            data.get('eligibility'),
            data.get('age_min') or None,
            data.get('age_max') or None,
            data.get('gender_specific'),
            data.get('occupation_specific'),
            data.get('category_specific'),
            data.get('income_limit') or None,
            data.get('required_documents'),
            data.get('benefits'),
            data.get('benefit_amount'),
            data.get('application_process'),
            data.get('district', 'State Wide'),
            True if data.get('is_state_wide') else False,
            data.get('official_link'),
            data.get('application_link'),
            data.get('helpline'),
            data.get('email'),
            data.get('office_address')
        ))
        
        flash('Scheme added successfully', 'success')
        return redirect(url_for('admin_schemes'))
    
    return render_template('admin/add_scheme.html')

@app.route('/admin/scheme/<int:scheme_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_scheme(scheme_id):
    """Edit scheme"""
    scheme = query_db("SELECT * FROM schemes WHERE id = %s", (scheme_id,), one=True)
    
    if not scheme:
        flash('Scheme not found', 'danger')
        return redirect(url_for('admin_schemes'))
    
    if request.method == 'POST':
        data = request.form
        
        query_db("""
            UPDATE schemes SET
                scheme_name = %s,
                category = %s,
                description = %s,
                eligibility = %s,
                age_min = %s,
                age_max = %s,
                gender_specific = %s,
                occupation_specific = %s,
                category_specific = %s,
                income_limit = %s,
                required_documents = %s,
                benefits = %s,
                benefit_amount = %s,
                application_process = %s,
                district = %s,
                is_state_wide = %s,
                official_link = %s,
                application_link = %s,
                helpline = %s,
                email = %s,
                office_address = %s
            WHERE id = %s
        """, (
            data.get('scheme_name'),
            data.get('category'),
            data.get('description'),
            data.get('eligibility'),
            data.get('age_min') or None,
            data.get('age_max') or None,
            data.get('gender_specific'),
            data.get('occupation_specific'),
            data.get('category_specific'),
            data.get('income_limit') or None,
            data.get('required_documents'),
            data.get('benefits'),
            data.get('benefit_amount'),
            data.get('application_process'),
            data.get('district'),
            True if data.get('is_state_wide') else False,
            data.get('official_link'),
            data.get('application_link'),
            data.get('helpline'),
            data.get('email'),
            data.get('office_address'),
            scheme_id
        ))
        
        flash('Scheme updated successfully', 'success')
        return redirect(url_for('admin_schemes'))
    
    return render_template('admin/edit_scheme.html', scheme=scheme)

@app.route('/admin/scheme/<int:scheme_id>/delete', methods=['POST'])
@admin_required
def admin_delete_scheme(scheme_id):
    """Delete scheme"""
    query_db("DELETE FROM schemes WHERE id = %s", (scheme_id,))
    flash('Scheme deleted successfully', 'success')
    return redirect(url_for('admin_schemes'))

@app.route('/admin/users')
@admin_required
def admin_users():
    """Manage users"""
    users_list = query_db("""
        SELECT * FROM users ORDER BY created_at DESC
    """)
    
    return render_template('admin/users.html', users=users_list)

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Analytics"""
    # Get statistics
    total_users = query_db("SELECT COUNT(*) as count FROM users", one=True)
    total_schemes = query_db("SELECT COUNT(*) as count FROM schemes WHERE is_active = 1", one=True)
    total_queries = query_db("SELECT COUNT(*) as count FROM chat_history", one=True)
    
    return render_template('admin/analytics.html',
        total_users=total_users,
        total_schemes=total_schemes,
        total_queries=total_queries
    )

@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    """View feedback"""
    feedback_list = query_db("""
        SELECT f.*, u.full_name FROM feedback f
        JOIN users u ON f.user_id = u.id
        ORDER BY f.created_at DESC
    """)
    
    return render_template('admin/feedback.html', feedback=feedback_list)

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('500.html'), 500

# ============================================
# UTILITY ROUTES
# ============================================

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Translate text to Tamil"""
    data = request.json
    text = data.get('text', '')
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Translate the following English text to Tamil. Provide only the translation."},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return jsonify({
            'original': text,
            'translated': response.choices[0].message.content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', True),
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000))
    )