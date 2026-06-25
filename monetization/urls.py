from django.urls import path
from . import views

app_name = 'monetization'

urlpatterns = [
    path('consent/', views.consent_view, name='consent'),
    path('premium-checkout/', views.premium_checkout, name='premium_checkout'),
    path('razorpay-callback/', views.razorpay_callback, name='razorpay_callback'),
    path('wallet/', views.wallet_view, name='wallet'),
]
