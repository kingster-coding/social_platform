from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url

class AccountAdapter(DefaultAccountAdapter):
    """
    WHAT: Custom Adapter to handle post-login/signup redirection
    WHY: Agar user verified nahi hai, toh use hamesha OTP page par bhejo
    """
    def get_login_redirect_url(self, request):
        """Login ke baad: unverified users ko OTP page pe bhejo"""
        user = request.user
        if hasattr(user, 'email_verified') and not user.email_verified:
            return resolve_url('accounts:verify_otp')
        return super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        """
        WHAT: Signup ke TURANT baad redirect URL
        WHY: Allauth ka dedicated hook — login redirect se alag hai.
             Naye user ko seedha OTP verify page pe bhejo.
        """
        return resolve_url('accounts:verify_otp')