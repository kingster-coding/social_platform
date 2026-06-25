"""
WHAT: URL patterns for search app
"""

from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.global_search, name='search'),
    path('quick/', views.quick_search, name='quick_search'),
]