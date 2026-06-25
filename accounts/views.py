from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import OTPVerificationForm
from .models import User

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
    """
    try:
        request.user.send_otp_email()
        messages.success(request, 'Naya OTP aapke email par bhej diya gaya hai.')
    except Exception as e:
        messages.error(request, 'Email bhejne mein problem hui. Thodi der baad try karein.')
    
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