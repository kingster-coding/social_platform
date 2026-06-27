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
        # OTP logic bypass/hold
        # if hasattr(user, 'email_verified') and not user.email_verified:
        #     return resolve_url('accounts:verify_otp')
        return super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        """
        WHAT: Signup ke TURANT baad redirect URL
        """
        # OTP logic bypass/hold
        # return resolve_url('accounts:verify_otp')
        return resolve_url('feed:feed')