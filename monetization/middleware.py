from django.shortcuts import redirect
from django.urls import reverse
from .models import UserConsent


class ConsentMiddleware:
    """
    WHAT: Ensures authenticated users select their monetization preference (Option A/B/C)
    WHY: Compliance validation showing investors that the platform is monetization-ready immediately.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # reverse() sirf ek baar compute hoga — har request pe nahi (performance fix)
        self.consent_url = reverse('monetization:consent')

    def __call__(self, request):
        # User signed-in hona chahiye aur verify_otp/email pages wagera ko ignore karenge
        if request.user.is_authenticated:
            # Allow static files, media, admin pages, auth pages, and consent itself
            # NOTE: /accounts/ prefix allauth + custom accounts dono ke liye allow hai
            #       Agar yeh missing ho toh login/signup pe bhi redirect loop ban jaati hai!
            allowed_paths = [
                self.consent_url,           # Consent page itself
                '/admin/',                  # Django admin
                '/static/',                 # Static files
                '/media/',                  # Media files
                '/accounts/',              # ALL auth paths: login, signup, logout, OTP, verify-email, password-reset, etc.
                '/monetization/razorpay-callback/',  # Payment callback
            ]

            # Check if current path matches any allowed prefix
            path_allowed = any(request.path.startswith(p) for p in allowed_paths)

            if not path_allowed:
                # Check if user has chosen their consent preference
                has_consent = UserConsent.objects.filter(user=request.user).exists()
                if not has_consent:
                    return redirect(self.consent_url)

        return self.get_response(request)

