from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles):
    """
    Decorator to ensure user has one of the allowed roles.
    If unauthorized, redirects user to their appropriate dashboard with a message.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('login')

            user_role = getattr(request.user, 'role', None)
            is_admin = request.user.is_superuser or user_role == 'ADMIN'

            if 'ADMIN' in allowed_roles and is_admin:
                return view_func(request, *args, **kwargs)

            if user_role not in allowed_roles:
                messages.error(request, f"Access denied. You do not have permissions for this section.")
                return redirect('dashboard_redirect')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def student_required(view_func):
    return role_required(['STUDENT'])(view_func)

def college_required(view_func):
    return role_required(['COLLEGE', 'ADMIN'])(view_func)

def recruiter_required(view_func):
    return role_required(['INDUSTRY', 'ADMIN'])(view_func)

def admin_required(view_func):
    return role_required(['ADMIN'])(view_func)

