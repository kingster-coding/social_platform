"""
WHAT: App configuration
WHY: Signals register karne ke liye ready() method use karte hain
"""
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'User Accounts'
    
    def ready(self):
        """
        WHAT: Import signals when app is ready
        WHY: Signals tabhi kaam karein jab app fully loaded ho
        """
        import accounts.signals