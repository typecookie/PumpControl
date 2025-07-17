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