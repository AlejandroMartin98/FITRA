from flask import Blueprint, render_template, session, redirect, url_for
chat_bp = Blueprint('chat', __name__, template_folder='templates')

@chat_bp.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('chat.html', username=session.get('username'))
