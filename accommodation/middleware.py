from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect

class RoleBasedSessionMiddleware(MiddlewareMixin):
    """
    Prevents session mixing between manager and customer
    by verifying role consistency on each request.
    """

    def process_request(self, request):
        user_session = request.session.get('user')
        if user_session:
            current_path = request.path

            # If a manager is on a customer page, redirect safely
            if 'manager' in current_path and user_session.get('role', '').lower() != 'manager':
                return redirect('room_list')

            # If a customer tries to access manager area
            if 'room_list' in current_path and user_session.get('role', '').lower() == 'manager':
                return redirect('manager_dashboard')
