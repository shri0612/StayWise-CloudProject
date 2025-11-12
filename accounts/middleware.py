from django.conf import settings

class DynamicSessionMiddleware:
    """
    Dynamically switches the session cookie name based on which cookie exists.
    Ensures manager and customer sessions stay isolated.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Detect which session cookie the browser sent
        if 'sessionid_manager' in request.COOKIES:
            request.session_cookie_name = 'sessionid_manager'
        elif 'sessionid_customer' in request.COOKIES:
            request.session_cookie_name = 'sessionid_customer'
        else:
            # Default fallback for unlogged or generic requests
            request.session_cookie_name = settings.SESSION_COOKIE_NAME

        response = self.get_response(request)

        
        if request.session.session_key:
            print(f" Active Session Middleware → Cookie: {request.session_cookie_name} | Key: {request.session.session_key}")

        return response
