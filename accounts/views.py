from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from functools import wraps
from accommodation.models import Profile
from accommodation.forms import RegisterForm, LoginForm
from accommodation.dynamo_users import add_user_to_dynamo, verify_user_credentials

# ======================================================
# ✅ Custom Login Decorator (for DynamoDB sessions)
# ======================================================
def login_required_dynamo(view_func):
    """Ensure user is logged in using DynamoDB session data."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user'):
            return redirect('login_user')
        return view_func(request, *args, **kwargs)
    return wrapper


# ======================================================
# ✅ Manager-only Decorator (for DynamoDB sessions)
# ======================================================
def manager_required(view_func):
    """Allow only managers (from DynamoDB) to access the view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.session.get('user')
        if not user:  # Not logged in
            return redirect('login_user')
        if user.get('role', '').lower() != 'manager':
            return redirect('room_list')
        return view_func(request, *args, **kwargs)
    return wrapper



# ======================================================
def register_user(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')

            # Create Profile in SQLite
            profile = Profile.objects.create(user=user, role=role)
            profile.save()

            # Add user to DynamoDB
            add_user_to_dynamo(user, role)

            messages.success(request, "Registration successful! Please log in.")
            return redirect('login_user')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# ======================================================
# 🔓 Login (DynamoDB-based)
# ======================================================
from django.contrib.sessions.models import Session

def login_user(request):
    """
    Handles login for both Manager and Customer using DynamoDB credentials.
    Creates separate cookies and prevents session overwrite.
    """
    # ✅ Clear any previous sessions
    logout(request)
    request.session.flush()

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password')

        user_data = verify_user_credentials(username_or_email, password)

        if user_data:
            role = user_data.get('role', '').lower()

            # ✅ Create a fresh session
            request.session.flush()
            request.session['user'] = {
                'username': user_data['username'],
                'email': user_data['email'],
                'role': role,
            }
            request.session['portal'] = role
            request.session.set_expiry(3600)  # 1 hour session timeout
            request.session.save()

            # ✅ Force new session key (ensures no overlap)
            request.session.cycle_key()

            # ✅ Prepare redirect based on role
            if role == 'manager':
                response = redirect('manager_dashboard')
                response.set_cookie(
                    'sessionid_manager',
                    request.session.session_key,
                    max_age=3600,
                    httponly=True,
                    samesite='Lax'
                )
                response.delete_cookie('sessionid_customer')
                response.delete_cookie('smarthost_session')

            else:
                response = redirect('room_list')
                response.set_cookie(
                    'sessionid_customer',
                    request.session.session_key,
                    max_age=3600,
                    httponly=True,
                    samesite='Lax'
                )
                response.delete_cookie('sessionid_manager')
                response.delete_cookie('smarthost_session')

            # ✅ Debug: print active session info
            print("🔹========================================")
            print(f"🔹 Logged in as: {user_data['username']} ({role})")
            print(f"🔹 Session Key: {request.session.session_key}")
            print(f"🔹 Cookie Assigned: sessionid_{role}")
            print("🔹========================================\n")

            return response

        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'accounts/login.html')


# ======================================================
# 🚪 Logout (Session-based)
# ======================================================
def logout_user(request):
    response = redirect('login_user')
    # ✅ Delete all possible session cookies
    response.delete_cookie('sessionid_manager')
    response.delete_cookie('sessionid_customer')
    response.delete_cookie('smarthost_session')
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")

    # ✅ Debug: confirm logout
    print("🚪 User logged out — all session cookies cleared.\n")
    return response
