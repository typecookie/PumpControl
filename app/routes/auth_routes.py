import os
import traceback

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ..utils.user_manager import UserManager
from ..models.user import UserRole

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print(f"Login attempt for user: {username}")

            user = UserManager.get_user_by_username(username)
            if not user:
                print("User not found")
                flash('Invalid username or password')
                return render_template('auth/login.html', UserRole=UserRole)

            if user.check_password(password):
                print("Password check passed, attempting login")
                login_user(user)
                next_page = request.args.get('next')
                print(f"Redirecting to: {next_page or 'main.index'}")
                return redirect(next_page or url_for('main.index'))

            print("Invalid password")
            flash('Invalid username or password')

        return render_template('auth/login.html', UserRole=UserRole)
    except Exception as e:
        print(f"Login error: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        flash('An error occurred during login. Please try again.')
        return render_template('auth/login.html', UserRole=UserRole), 500


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/users')
@login_required
def user_list():
    if not current_user.has_role(UserRole.ADMINISTRATOR):
        flash('Access denied')
        return redirect(url_for('main.index'))
    return render_template('auth/users.html', users=UserManager._users.values(), UserRole=UserRole)

@bp.route('/users/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.has_role(UserRole.ADMINISTRATOR):
        flash('Access denied')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        try:
            UserManager.create_user(
                username=request.form['username'],
                password=request.form['password'],
                role=UserRole(request.form['role'])
            )
            flash('User created successfully')
            return redirect(url_for('auth.user_list'))
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            print(traceback.format_exc())
            flash(f'Error creating user: {str(e)}')
            return render_template('auth/create_user.html', roles=UserRole, UserRole=UserRole)

    return render_template('auth/create_user.html', roles=UserRole, UserRole=UserRole)


@bp.route('/test')
def test():
    return render_template('base.html')

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.has_role(UserRole.ADMINISTRATOR):
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    # Prevent administrators from deleting their own account
    if user_id == current_user.id:
        flash('You cannot delete your own account')
        return redirect(url_for('auth.user_list'))

    # Check if this is the last administrator
    user_to_delete = UserManager.get_user_by_id(user_id)
    if user_to_delete and user_to_delete.role == UserRole.ADMINISTRATOR:
        admin_count = sum(1 for user in UserManager.get_all_users() if user.role == UserRole.ADMINISTRATOR)
        if admin_count <= 1:
            flash('Cannot delete the last administrator account')
            return redirect(url_for('auth.user_list'))
    
    result = UserManager.delete_user(user_id)
    if result:
        flash('User deleted successfully')
    else:
        flash('User not found')
    
    return redirect(url_for('auth.user_list'))

@bp.route('/users/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def reset_password(user_id):
    if not current_user.has_role(UserRole.ADMINISTRATOR):
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    user = UserManager.get_user_by_id(user_id)
    if not user:
        flash('User not found')
        return redirect(url_for('auth.user_list'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password:
            flash('Password cannot be empty')
            return render_template('auth/reset_password.html', user=user, UserRole=UserRole)
        
        if new_password != confirm_password:
            flash('Passwords do not match')
            return render_template('auth/reset_password.html', user=user, UserRole=UserRole)
        
        try:
            UserManager.reset_password(user_id, new_password)
            flash(f'Password for {user.username} has been reset successfully')
            return redirect(url_for('auth.user_list'))
        except Exception as e:
            print(f"Error resetting password: {str(e)}")
            print(traceback.format_exc())
            flash(f'Error resetting password: {str(e)}')
    
    return render_template('auth/reset_password.html', user=user, UserRole=UserRole)

@bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.has_role(UserRole.ADMINISTRATOR):
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    user = UserManager.get_user_by_id(user_id)
    if not user:
        flash('User not found')
        return redirect(url_for('auth.user_list'))
    
    if request.method == 'POST':
        new_role = UserRole(request.form.get('role'))
        
        # Check if this is the last administrator
        if user.role == UserRole.ADMINISTRATOR and new_role != UserRole.ADMINISTRATOR:
            admin_count = sum(1 for u in UserManager.get_all_users() if u.role == UserRole.ADMINISTRATOR)
            if admin_count <= 1:
                flash('Cannot change the role of the last administrator')
                return redirect(url_for('auth.user_list'))
        
        try:
            UserManager.update_user_role(user_id, new_role)
            flash(f'Role for {user.username} has been updated successfully')
            return redirect(url_for('auth.user_list'))
        except Exception as e:
            print(f"Error updating user role: {str(e)}")
            print(traceback.format_exc())
            flash(f'Error updating user role: {str(e)}')
    
    return render_template('auth/edit_user.html', user=user, roles=UserRole, UserRole=UserRole)