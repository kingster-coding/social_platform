"""
Core views - temporary home page jab tak feed app ready nahi hoti.
"""

from django.shortcuts import render

def home(request):
    """
    WHAT: Temporary home page view
    WHY: Home URL ke liye kuch toh dikhana padega jab tak feed app na ban jaye
    """
    context = {
        'page_title': 'Home',
    }
    return render(request, 'home.html', context)