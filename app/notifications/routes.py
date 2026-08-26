"""Notification routes — list, mark read."""
from flask import render_template, redirect, url_for, jsonify, request
from flask_login import current_user, login_required

from . import notifications_bp
from ..extensions import db
from ..models.notification import Notification
from ..utils.helpers import paginate_query


@notifications_bp.route('/')
@login_required
def list_notifications():
    notifications = paginate_query(
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc()),
        per_page=20,
    )
    return render_template(
        'notifications/list.html', title='Notifications', notifications=notifications,
    )


@notifications_bp.route('/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.mark_read()
    db.session.commit()

    if notif.link:
        return redirect(notif.link)
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/api/count')
@login_required
def api_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})
