from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url

class AccountAdapter(DefaultAccountAdapter):
    """
    WHAT: Custom Adapter to handle post-login/signup redirection
    WHY: Agar user verified nahi hai, toh use hamesha OTP page par bhejo
    """
    def get_login_redirect_url(self, request):
        user = request.user
        if hasattr(user, 'email_verified') and not user.email_verified:
            return resolve_url('accounts:verify_otp')
        return super().get_login_redirect_url(request)