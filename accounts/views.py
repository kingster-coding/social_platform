from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import random
import json

from .forms import OTPVerificationForm, RegisterStep1Form
from .models import User


# ============================================
# REGISTRATION — 2 PHASE FLOW
# ============================================

def register_view(request):
    """
    WHAT: Custom registration page — replaces allauth default signup
    WHY: We need full_name + phone_number + auto-generated username
    Renders the signup template with our custom RegisterStep1Form.
    AJAX endpoints handle OTP send + verify.
    """
    # If already logged in, go to feed
    if request.user.is_authenticated:
        return redirect('feed:feed')

    form = RegisterStep1Form()
    return render(request, 'account/signup.html', {'form': form})


def register_send_otp(request):
    """
    WHAT: AJAX endpoint — Phase 1
    1. Validate form (name, email, phone, password)
    2. Store validated data in session (password hashed)
    3. Generate OTP, store in session, email it
    4. Return JSON success/error
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    form = RegisterStep1Form(request.POST)
    if not form.is_valid():
        # Collect all errors
        errors = {}
        for field, errs in form.errors.items():
            errors[field] = [str(e) for e in errs]
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    cd = form.cleaned_data

    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    otp_expiry = (timezone.now() + timedelta(minutes=10)).isoformat()

    # Store in session (password hashed, never plain text)
    request.session['reg_data'] = {
        'first_name': cd['first_name'],
        'last_name': cd['last_name'],
        'email': cd['email'],
        'phone_number': cd['phone_number'],
        'password_hash': make_password(cd['password1']),
        'otp': otp_code,
        'otp_expiry': otp_expiry,
    }
    request.session.modified = True

    # Send OTP email
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives
    full_name = f"{cd['first_name']} {cd['last_name']}"
    masked_email = cd['email'][:3] + '***@' + cd['email'].split('@')[1]

    text_content = (
        f"Hi {full_name},\n\n"
        f"Your OTP for account verification is: {otp_code}\n\n"
        f"This OTP is valid for 10 minutes.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"— Social Platform Team"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#f4f6fb;font-family:'Segoe UI',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fb;padding:40px 0;">
        <tr><td align="center">
          <table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#1877f2,#58a6ff);padding:32px;text-align:center;">
                <div style="font-size:40px;margin-bottom:12px;">🔐</div>
                <h1 style="color:#ffffff;font-size:22px;font-weight:800;margin:0;">Verify Your Account</h1>
                <p style="color:rgba(255,255,255,0.8);font-size:14px;margin:6px 0 0;">Social Platform</p>
              </td>
            </tr>
            <tr>
              <td style="padding:36px 40px;">
                <p style="color:#374151;font-size:16px;margin:0 0 8px;">Hi <strong>{full_name}</strong>,</p>
                <p style="color:#6b7280;font-size:14px;margin:0 0 28px;line-height:1.6;">
                  Aapne Social Platform par account verify karne ki request ki hai. Neeche diya gaya OTP use karein:
                </p>
                <div style="background:#f0f7ff;border:2px dashed #1877f2;border-radius:12px;padding:24px;text-align:center;margin:0 0 28px;">
                  <p style="color:#6b7280;font-size:12px;font-weight:600;letter-spacing:1px;margin:0 0 8px;text-transform:uppercase;">Your OTP</p>
                  <div style="font-size:42px;font-weight:800;letter-spacing:12px;color:#1877f2;font-family:'Courier New',monospace;">{otp_code}</div>
                  <p style="color:#ef4444;font-size:12px;margin:10px 0 0;">⏱ Valid for 10 minutes only</p>
                </div>
                <p style="color:#9ca3af;font-size:12px;margin:0;line-height:1.6;">
                  Agar aapne yeh request nahi ki hai, toh is email ko ignore kar dein.
                </p>
              </td>
            </tr>
            <tr>
              <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
                <p style="color:#9ca3af;font-size:12px;margin:0;">© 2025 Social Platform. All rights reserved.</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    try:
        email_msg = EmailMultiAlternatives(
            subject='🔐 Verify Your Account — OTP',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[cd['email']]
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send(fail_silently=False)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Email bhejne mein dikkat hui. Phir try karein.'}, status=500)

    return JsonResponse({
        'success': True,
        'masked_email': masked_email,
        'message': f'OTP {masked_email} par bhej diya gaya hai.'
    })


def register_verify_otp(request):
    """
    WHAT: AJAX endpoint — Phase 2
    1. Verify OTP from session
    2. Create user account with auto-generated username
    3. Log them in
    4. Return JSON with redirect URL
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    reg_data = request.session.get('reg_data')
    if not reg_data:
        return JsonResponse({
            'success': False,
            'error': 'Session expired. Please fill the form again.'
        }, status=400)

    try:
        body = json.loads(request.body)
        entered_otp = body.get('otp', '').strip()
    except (json.JSONDecodeError, AttributeError):
        entered_otp = request.POST.get('otp', '').strip()

    # OTP check
    stored_otp = reg_data.get('otp')
    otp_expiry_str = reg_data.get('otp_expiry')

    if not stored_otp or stored_otp != entered_otp:
        return JsonResponse({'success': False, 'error': 'Galat OTP. Dobara check karein.'}, status=400)

    # Expiry check
    from django.utils.dateparse import parse_datetime
    otp_expiry = parse_datetime(otp_expiry_str)
    if otp_expiry and timezone.now() > otp_expiry:
        return JsonResponse({'success': False, 'error': 'OTP expire ho gaya. Phir se OTP mangayein.'}, status=400)

    # Create user
    try:
        full_name = f"{reg_data['first_name']} {reg_data['last_name']}"
        auto_username = User.generate_auto_username(
            full_name=full_name,
            email=reg_data['email'],
            phone=reg_data['phone_number']
        )

        user = User(
            username=auto_username,
            email=reg_data['email'],
            first_name=reg_data['first_name'],
            last_name=reg_data['last_name'],
            phone_number=reg_data['phone_number'],
            email_verified=True,
            username_locked=True,
            coins=0,
        )
        user.password = reg_data['password_hash']
        user.save()

        # Create linked Profile
        from .models import Profile
        Profile.objects.get_or_create(user=user)

        # Clear session
        del request.session['reg_data']
        request.session.modified = True

        # Log them in
        from django.contrib.auth import login as auth_login
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth_login(request, user)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Account create karne mein dikkat hui: {str(e)}'}, status=500)

    return JsonResponse({
        'success': True,
        'username': user.username,
        'redirect': '/feed/'
    })


def username_preview(request):
    """
    WHAT: AJAX GET endpoint — live username preview
    WHY: User ko form par hi dikhana hai ki unka username kya hoga
    """
    full_name = request.GET.get('full_name', '').strip()
    email = request.GET.get('email', '').strip()
    phone = request.GET.get('phone', '').strip()

    if not full_name or not phone:
        return JsonResponse({'username': ''})

    # Generate preview (don't save, just preview)
    import re
    import unicodedata

    def slugify(text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'[^a-zA-Z0-9 ]', '', text).strip().lower()
        return text

    parts = full_name.split()
    first = slugify(parts[0]) if parts else 'user'
    last_initial = slugify(parts[-1])[0] if len(parts) > 1 and parts[-1] else ''

    digits = re.sub(r'\D', '', phone)
    last4 = digits[-4:] if len(digits) >= 4 else digits.zfill(4)

    import random
    sc = random.choice(['.', '_', '#'])
    rand_suffix = str(random.randint(10, 99))

    if last_initial:
        preview = f"{first}{sc}{last_initial}#{last4}_{rand_suffix}"
    else:
        preview = f"{first}#{last4}_{rand_suffix}"

    return JsonResponse({'username': preview})

@login_required
def profile_view(request, username=None):
    """
    WHAT: User ka profile dikhane ke liye
    """
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user
        
    is_own_profile = (profile_user == request.user)
    
    # Try to get the profile or create it if missing
    from .models import Profile
    profile, _ = Profile.objects.get_or_create(user=profile_user)
    
    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)

from .forms import UserProfileForm

@login_required
def profile_edit(request):
    """
    WHAT: View to edit custom User and Profile details
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile successfully update ho gaya!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
        
    context = {
        'form': form,
    }
    return render(request, 'accounts/profile_edit.html', context)

from .forms import UserSettingsForm
from monetization.models import UserConsent

@login_required
def profile_settings(request):
    """
    WHAT: View to manage account settings, privacy, and consent preferences
    """
    consent = UserConsent.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings update ho gayi hain!')
            return redirect('accounts:settings')
    else:
        form = UserSettingsForm(instance=request.user)
        
    context = {
        'form': form,
        'consent': consent,
    }
    return render(request, 'accounts/settings.html', context)

@login_required
def verify_email_view(request):
    """
    WHAT: View to handle OTP input and verification
    """
    # Agar pehle se verified hai toh home bhej do
    if request.user.email_verified:
        return redirect('feed:feed')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp')
            if request.user.verify_otp(otp_code):
                messages.success(request, 'Account successfully verify ho gaya! Welcome.')
                return redirect('feed:feed')
            else:
                messages.error(request, 'Invalid ya expired OTP. Phir se koshish karein.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'accounts/verify_otp.html', {'form': form})

@login_required
def resend_otp_view(request):
    """
    WHAT: Resend OTP email logic
    WHY: AJAX aur normal dono requests handle karta hai
         - AJAX (fetch): JSON response return karta hai (countdown timer ke liye)
         - Normal GET: redirect karta hai
    """
    from django.http import JsonResponse
    
    try:
        request.user.send_otp_email()
        success = True
        msg = 'Naya OTP aapke email par bhej diya gaya hai.'
    except Exception as e:
        success = False
        msg = 'Email bhejne mein problem hui. Thodi der baad try karein.'
    
    # AJAX request check (fetch API ya XMLHttpRequest)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               request.headers.get('Accept') == 'application/json'
    
    if is_ajax:
        return JsonResponse({'success': success, 'message': msg})
    
    # Normal request — purana behavior
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('accounts:verify_otp')

from django.http import HttpResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def follow_unfollow(request, username):
    """
    WHAT: Follow/Unfollow user toggle with HTMX compatibility
    """
    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        messages.error(request, 'Aap khud ko follow nahi kar sakte.')
        return redirect('accounts:profile_detail', username=username)
        
    if request.user.following.filter(pk=target_user.pk).exists():
        request.user.following.remove(target_user)
        followed = False
        messages.info(request, f'You unfollowed {target_user.username}.')
    else:
        request.user.following.add(target_user)
        followed = True
        messages.success(request, f'You are now following {target_user.username}!')
        
        # Trigger notification
        from user_notifications.utils import notify_user
        notify_user(
            recipient=target_user,
            notification_type='follow',
            title='New Follower',
            message=f'{request.user.username} is now following you.',
            actor=request.user,
            url=f'/accounts/profile/{request.user.username}/'
        )
        
    if request.headers.get('HX-Request'):
        label = "Following" if followed else "Follow"
        style = "padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 700; border: 1px solid var(--border-color); background: var(--hover-bg); color: var(--text-primary); cursor: pointer;" if followed else "padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 700; border: none; background: var(--accent-color); color: white; cursor: pointer;"
        return HttpResponse(f'<button type="submit" style="{style}">{label}</button>')
        
    return redirect(request.META.get('HTTP_REFERER', 'feed:feed'))


def debug_email_view(request):
    """
    WHAT: Diagnostic view to check email configuration and send a test email.
    """
    from django.conf import settings
    from django.core.mail import send_mail
    import traceback

    # Mask password
    pw = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    masked_pw = f"{pw[:2]}...{pw[-2:]}" if len(pw) > 4 else ("Set" if pw else "Not Set")

    info = {
        'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', None),
        'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', None),
        'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', None),
        'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', None),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', None),
        'EMAIL_HOST_PASSWORD': masked_pw,
        'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', None),
    }

    test_status = "Not attempted"
    error_trace = ""
    
    email_to = request.GET.get('email', 'kingster383@gmail.com')

    try:
        res = send_mail(
            subject="Diagnostic Test Email",
            message="This is a diagnostic email from your Social Platform project.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_to],
            fail_silently=False
        )
        test_status = f"Success! send_mail returned {res}"
    except Exception as e:
        test_status = f"Failed: {type(e).__name__} - {str(e)}"
        error_trace = traceback.format_exc()

    return JsonResponse({
        'success': 'Failed' not in test_status,
        'info': info,
        'test_status': test_status,
        'error_trace': error_trace
    })
