from flask import Blueprint, render_template, redirect, url_for, flash, request, abort  # Added missing imports
from flask_login import login_required, current_user
from app.models.user import User
from app.models.quote import Quote
from app.extensions import db  # Added db import

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        abort(403)
    
    filter_type = request.args.get('filter', 'all')
    
    query = Quote.query
    
    if filter_type == 'approved':
        query = query.filter_by(approved=True)
    elif filter_type == 'pending':
        query = query.filter_by(approved=False)
    
    quotes = query.order_by(Quote.id.desc()).all()
    return render_template('admin/dashboard.html', quotes=quotes, filter_type=filter_type)



@admin_bp.route('/admin/add-quote', methods=['GET', 'POST'])
@login_required
def add_quote():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        content = request.form['content']
        author = request.form['author']
        new_quote = Quote(content=content, author=author, approved=True)
        db.session.add(new_quote)
        db.session.commit()
        flash('Quote added successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/add_quote.html')

@admin_bp.route('/admin/manage-users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/admin/delete-user/<int:id>')
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    
    user = User.query.get(id)
    if user and user.id != current_user.id:  # Prevent self-deletion
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/delete-quote/<int:id>')
@login_required
def delete_quote(id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    
    quote = Quote.query.get(id)
    if quote:
        db.session.delete(quote)
        db.session.commit()
        flash('Quote deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/edit-quote/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_quote(id):
    if current_user.role != 'admin':
        abort(403)
    
    quote = Quote.query.get_or_404(id)
    
    if request.method == 'POST':
        quote.content = request.form['content']
        quote.author = request.form['author']
        quote.approved = request.form.get('approved') == 'true'
        db.session.commit()
        flash('Quote updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/edit_quote.html', quote=quote)



@admin_bp.before_request
@login_required
def check_admin():
    if current_user.role != 'admin':
        abort(403)




@admin_bp.route('/admin/approve-quote/<int:id>')
@login_required
def approve_quote(id):
    if current_user.role != 'admin':
        abort(403)
    
    quote = Quote.query.get_or_404(id)
    quote.approved = True
    db.session.commit()
    flash('Quote approved successfully!', 'success')
    return redirect_back()

@admin_bp.route('/admin/unapprove-quote/<int:id>')
@login_required
def unapprove_quote(id):
    if current_user.role != 'admin':
        abort(403)
    
    quote = Quote.query.get_or_404(id)
    quote.approved = False
    db.session.commit()
    flash('Quote unapproved successfully!', 'warning')
    return redirect_back()

def redirect_back(default='admin.dashboard'):
    return redirect(request.referrer or url_for(default))
