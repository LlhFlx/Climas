import datetime
from django.conf import settings
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin

class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            now = datetime.datetime.now()
            last_activity_str = request.session.get('last_activity')

            # Get timeout from settings (default: 15 minutes)
            timeout_seconds = getattr(settings, 'AUTO_LOGOUT_DELAY', 15 * 60)

            if last_activity_str:
                try:
                    last_activity = datetime.datetime.fromisoformat(last_activity_str)
                    if (now - last_activity).total_seconds() > timeout_seconds:
                        logout(request)
                        request.session.flush()
                        return
                except ValueError:
                    # Invalid timestamp format — treat as expired
                    logout(request)
                    request.session.flush()
                    return

            # Update last activity
            request.session['last_activity'] = now.isoformat()