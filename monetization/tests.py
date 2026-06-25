from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from .models import UserConsent, Subscription

User = get_user_model()


class MonetizationAppTests(TestCase):
    """
    WHAT: Automated tests for GDPR Consent and Razorpay monetization
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='monetized_user',
            email='muser@social.com',
            password='Password123'
        )

    def test_consent_view_requires_login(self):
        """Verify redirect to login for unauthenticated users on consent page"""
        response = self.client.get(reverse('monetization:consent'))
        self.assertNotEqual(response.status_code, 200)

    def test_set_consent_option_a_ads(self):
        """Verify setting consent Option A (Ad-Supported) works"""
        self.client.login(email='muser@social.com', password='Password123')
        response = self.client.post(
            reverse('monetization:consent'),
            {'consent_type': 'ads'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        consent = UserConsent.objects.get(user=self.user)
        self.assertEqual(consent.consent_type, 'ads')

    def test_set_consent_option_c_data(self):
        """Verify setting consent Option C (sell data for credits) works"""
        self.client.login(email='muser@social.com', password='Password123')
        response = self.client.post(
            reverse('monetization:consent'),
            {'consent_type': 'data'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        consent = UserConsent.objects.get(user=self.user)
        self.assertEqual(consent.consent_type, 'data')

        # Check that wallet displays the reward credits
        wallet_response = self.client.get(reverse('monetization:wallet'))
        self.assertEqual(wallet_response.status_code, 200)
        self.assertContains(wallet_response, "120.00")

    def test_razorpay_checkout_redirects_to_premium(self):
        """Verify selecting Option B redirects to payment checkout"""
        self.client.login(email='muser@social.com', password='Password123')
        response = self.client.post(
            reverse('monetization:consent'),
            {'consent_type': 'premium'}
        )
        self.assertRedirects(response, reverse('monetization:premium_checkout'))

    def test_razorpay_callback_activates_subscription(self):
        """Verify mock payment callback successfully activates Premium subscription"""
        self.client.login(email='muser@social.com', password='Password123')
        # Simulate choosing Option B first (creating consent record)
        UserConsent.objects.create(user=self.user, consent_type='premium')
        response = self.client.post(
            reverse('monetization:razorpay_callback'),
            {
                'razorpay_payment_id': 'pay_test_payment_123',
                'razorpay_order_id': 'order_test_order_123'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subscription.objects.filter(user=self.user, status='active').count(), 1)
        
        # Verify user consent type automatically updated to premium
        consent = UserConsent.objects.get(user=self.user)
        self.assertEqual(consent.consent_type, 'premium')
