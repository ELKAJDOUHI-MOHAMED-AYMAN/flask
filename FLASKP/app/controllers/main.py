from flask import Blueprint, render_template, jsonify, request, current_app, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.models.quote import Quote
from app.extensions import cache, db
import requests
import random
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from app.config import allowed_file
from app.models.user import User
from app.models.quote import Rating


main_bp = Blueprint('main', __name__)

# Enhanced quote APIs with better fallbacks
QUOTE_APIS = [
    {
        'name': 'Quotable',
        'url': 'https://api.quotable.io/random',
        'parser': lambda data: (data['content'], data['author'], 'Quotable API'),
        'test_url': 'https://api.quotable.io/random',
        'headers': {'User-Agent': 'QuoteMaster/1.0'}
    },
    {
        'name': 'They Said So',
        'url': 'https://quotes.rest/qod.json',
        'parser': lambda data: (data['contents']['quotes'][0]['quote'],
                              data['contents']['quotes'][0]['author'],
                              'They Said So'),
        'headers': {'Accept': 'application/json'}
    },
    {
        'name': 'Programming Quotes',
        'url': 'https://programming-quotes-api.herokuapp.com/quotes/random',
        'parser': lambda data: (data['en'], data['author'], 'Programming Quotes')
    },
    {
        'name': 'Forismatic',
        'url': 'https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en',
        'parser': lambda data: (data['quoteText'].strip(), 
                              data['quoteAuthor'] or 'Unknown', 
                              'Forismatic API')
    }
]

FALLBACK_QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Life is what happens when you're busy making other plans.", "John Lennon"),
    ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("Your time is limited, don't waste it living someone else's life.", "Steve Jobs")
]

def get_working_apis():
    working_apis = []
    for api in QUOTE_APIS:
        try:
            test_url = api.get('test_url', api['url'])
            response = requests.get(
                test_url,
                timeout=2,
                headers=api.get('headers', {'User-Agent': 'QuoteMaster/1.0'}))
            if response.status_code == 200:
                working_apis.append(api)
        except:
            continue
    return working_apis if working_apis else QUOTE_APIS  # Fallback to all if none respond

def fetch_quote_from_api(api):
    try:
        response = requests.get(
            api['url'],
            timeout=2,
            headers=api.get('headers', {'User-Agent': 'QuoteMaster/1.0'}))
        response.raise_for_status()
        data = response.json()
        content, author, source = api['parser'](data)
        return {
            'content': content,
            'author': author,
            'source': source,
            'status': 'api',
            'timestamp': datetime.now().isoformat()
        }
    except:
        return None

def get_fresh_quote():
    working_apis = get_working_apis()
    random.shuffle(working_apis)  # Randomize API selection
    
    for api in working_apis:
        quote = fetch_quote_from_api(api)
        if quote:
            return jsonify(quote)
    
    # Fallback to hardcoded quotes if all APIs fail
    content, author = random.choice(FALLBACK_QUOTES)
    return jsonify({
        'content': content,
        'author': author,
        'source': 'Fallback Quotes',
        'status': 'fallback',
        'timestamp': datetime.now().isoformat()
    })

@main_bp.route('/api/external-random-quote')
def external_random_quote():
    if 'nocache' in request.args:
        return get_fresh_quote()
    return cached_external_quote()

@cache.cached(timeout=10)
def cached_external_quote():
    return get_fresh_quote()

@main_bp.route('/')
def home():
    return render_template('main/home.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    quotes = Quote.query.filter_by(user_id=current_user.id).all()
    return render_template('user/dashboard.html', quotes=quotes)

@main_bp.route('/api/random-quotes')
@cache.cached(timeout=60)
def random_quotes():
    try:
        count = min(int(request.args.get('count', 3)), 20)
        quotes = Quote.query.filter_by(approved=True).order_by(db.func.random()).limit(count).all()
        return jsonify([q.serialize() for q in quotes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/quotes/search')
def search_quotes():
    try:
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify([])
        
        quotes = Quote.query.filter(
            (Quote.content.ilike(f'%{search_term}%')) | 
            (Quote.author.ilike(f'%{search_term}%'))
        ).limit(12).all()
        
        return jsonify([q.serialize() for q in quotes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# Profile update

@main_bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html')

@main_bp.route('/api/update-username', methods=['POST'])
@login_required
def update_username():
    new_username = request.json.get('username')
    if User.query.filter_by(username=new_username).first():
        return jsonify({'success': False, 'error': 'Username already taken'})
    current_user.username = new_username
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/api/update-password', methods=['POST'])
@login_required
def update_password():
    data = request.json
    if not current_user.check_password(data['current_password']):
        return jsonify({'success': False, 'error': 'Current password is incorrect'})
    current_user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/api/update-avatar', methods=['POST'])
@login_required
def update_avatar():
    try:
        print("\n=== AVATAR UPLOAD ATTEMPT ===")
        
        if 'avatar' not in request.files:
            print("No 'avatar' in request.files")
            return jsonify({'success': False, 'error': 'No file selected'})
            
        file = request.files['avatar']
        print(f"Received file: {file.filename}")
        
        if file.filename == '':
            print("Empty filename")
            return jsonify({'success': False, 'error': 'No file selected'})
            
        if not allowed_file(file.filename):
            print("Invalid file type")
            return jsonify({'success': False, 'error': 'Invalid file type'})

        # Ensure upload folder exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        print(f"Upload folder: {upload_folder}")
        
        # Save file
        filename = secure_filename(f"user_{current_user.id}_{file.filename}")
        filepath = os.path.join(upload_folder, filename)
        print(f"Saving to: {filepath}")
        file.save(filepath)
        
        # Update user
        current_user.profile_image = filename
        db.session.commit()
        
        return jsonify({
            'success': True,
            'avatar_url': current_user.get_profile_image()
        })
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error during upload'})
    



# In main.py
@main_bp.route('/quotes')
def browse_quotes():
    # Pass empty quote variable explicitly
    return render_template('main/quotes.html', quote=None)

@main_bp.route('/quotes/<int:id>')
def quote_detail(id):
    quote = Quote.query.get_or_404(id)
    user_rating = None
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(
            user_id=current_user.id, 
            quote_id=id
        ).first()
    return render_template('main/quote.html', 
                         quote=quote,
                         user_rating=user_rating)

    


# In main.py
@main_bp.route('/propose-quote', methods=['GET', 'POST'])
@login_required
def propose_quote():
    if request.method == 'POST':
        content = request.form['content']
        author = request.form['author']
        new_quote = Quote(
            content=content,
            author=author,
            approved=False,
            user_id=current_user.id
        )
        db.session.add(new_quote)
        db.session.commit()
        flash('Quote submitted for approval!', 'success')
        return redirect(url_for('main.browse_quotes'))
    return render_template('main/propose_quote.html')

# Remove this route if not needed elsewhere
@main_bp.route('/user/quotes')
@login_required
def user_quotes():
    quotes = Quote.query.filter_by(user_id=current_user.id).all()
    return render_template('user/dashboard.html', quotes=quotes)  # Or remove completely



# In main.py
@main_bp.route('/edit-quote/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_quote(id):
    quote = Quote.query.get_or_404(id)
    if quote.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        quote.content = request.form['content']
        quote.author = request.form['author']
        db.session.commit()
        flash('Quote updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))  # Changed from user_quotes to dashboard
    
    return render_template('user/edit_quote.html', quote=quote)

@main_bp.route('/delete-quote/<int:id>')
@login_required
def delete_quote(id):
    quote = Quote.query.get_or_404(id)
    if quote.user_id != current_user.id:
        abort(403)
    
    db.session.delete(quote)
    db.session.commit()
    flash('Quote deleted successfully!', 'success')
    return redirect(url_for('main.dashboard'))  # Changed from user_quotes to dashboard


@main_bp.route('/api/quotes')
def get_paginated_quotes():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 9
        
        quotes = Quote.query.filter_by(approved=True)\
                  .order_by(Quote.id.desc())\
                  .paginate(page=page, per_page=per_page)
        
        return jsonify([q.serialize() for q in quotes.items])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


# main.py
@main_bp.route('/api/quote/<int:quote_id>/rate', methods=['POST'])
@login_required
def rate_quote(quote_id):
    data = request.get_json()
    rating_value = data.get('rating')

    if not rating_value or not (1 <= rating_value <=5):
        return jsonify({'error': 'Invalid rating value'}), 400

    quote = Quote.query.get_or_404(quote_id)
    existing_rating = Rating.query.filter_by(user_id=current_user.id, quote_id=quote_id).first()

    if existing_rating:
        existing_rating.value = rating_value
    else:
        new_rating = Rating(user_id=current_user.id, quote_id=quote_id, value=rating_value)
        db.session.add(new_rating)

    # Recalculate average
    ratings = [r.value for r in quote.ratings]
    quote.average_rating = sum(ratings) / len(ratings) if ratings else 0
    db.session.commit()

    return jsonify({
        'success': True,
        'average_rating': round(quote.average_rating, 1)
    })


# main.py
@main_bp.route('/quotes/popular')
def popular_quotes():
    popular_quotes = Quote.query.filter(
        Quote.average_rating >= 3.0,
        Quote.approved == True
    ).order_by(Quote.average_rating.desc()).all()
    return render_template('main/popular_quotes.html', quotes=popular_quotes)

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html')