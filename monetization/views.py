from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import UserConsent, Subscription


@login_required
def consent_view(request):
    """
    WHAT: Option A, B, C Monetization Consent Selection View
    WHY: Required for user to choose how they support the platform
    """
    # Check if consent already exists
    user_consent = UserConsent.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        consent_type = request.POST.get('consent_type')
        if consent_type in ['ads', 'premium', 'data']:
            if not user_consent:
                user_consent = UserConsent(user=request.user)
            user_consent.consent_type = consent_type
            user_consent.save()
            
            messages.success(request, f"Preferences saved! Option: {user_consent.get_consent_type_display()}")
            
            if consent_type == 'premium':
                # Redirect to payment checkout flow
                return redirect('monetization:premium_checkout')
            
            return redirect('feed:feed')
            
    context = {
        'user_consent': user_consent,
    }
    return render(request, 'monetization/consent.html', context)


@login_required
def premium_checkout(request):
    """
    WHAT: Subscription checkout with simulated Razorpay Integration
    WHY: Show investor monetization dashboard with simulated transaction
    """
    # Check if they already have an active subscription
    active_sub = Subscription.objects.filter(user=request.user, status='active').first()
    if active_sub and active_sub.is_valid:
        messages.info(request, "Aapka Premium Subscription pehle se active hai!")
        return redirect('feed:feed')

    context = {
        'price': 299, # INR monthly cost
        'key_id': 'rzp_test_mockkey12345', # Mock Razorpay Key
    }
    return render(request, 'monetization/premium_checkout.html', context)


@login_required
def razorpay_callback(request):
    """
    WHAT: Callback simulation for Razorpay payment success
    WHY: Mock payment status confirmation and subscription generation
    """
    if request.method == 'POST':
        # Simulated payment completion
        payment_id = request.POST.get('razorpay_payment_id', 'pay_mock_' + str(int(timezone.now().timestamp())))
        order_id = request.POST.get('razorpay_order_id', 'order_mock_12345')
        
        # Create active subscription for 30 days
        sub = Subscription.objects.create(
            user=request.user,
            status='active',
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        
        # Make sure user consent is set to premium
        consent, _ = UserConsent.objects.get_or_create(user=request.user)
        consent.consent_type = 'premium'
        consent.save()

        messages.success(request, "Premium Subscription Activated successfully via Razorpay!")
        return JsonResponse({'status': 'success', 'redirect_url': '/'})

    return JsonResponse({'status': 'failed'}, status=400)


@login_required
def wallet_view(request):
    """
    WHAT: Shows credits for Option C (Sell Data for Wallet Credits)
    WHY: Engagement model validation
    """
    consent = UserConsent.objects.filter(user=request.user).first()
    is_data_opt_in = consent and consent.consent_type == 'data'
    
    # Calculate mock balance based on profile state/activity
    credits = 120.00 if is_data_opt_in else 0.00
    
    context = {
        'is_data_opt_in': is_data_opt_in,
        'credits': credits,
    }
    return render(request, 'monetization/wallet.html', context)
