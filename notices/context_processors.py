def notifications(request):
    """Makes the unread notification count and recent notifications available
    to every template (used for the bell icon in the header)."""
    if not request.user.is_authenticated:
        return {}
    recent = request.user.notifications.select_related("actor", "notice")[:6]
    return {
        "unread_notification_count": request.user.notifications.filter(is_read=False).count(),
        "recent_notifications": recent,
    }