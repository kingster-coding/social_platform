"""
WHAT: URL patterns for reels app
"""

from django.urls import path
from . import views

app_name = 'reels'

urlpatterns = [
    path('', views.reels_feed, name='feed'),
    path('upload/', views.upload_reel, name='upload'),
    path('<int:pk>/', views.reel_detail, name='reel_detail'),
    path('<int:pk>/like/', views.like_reel, name='like'),
    path('<int:pk>/save/', views.save_reel, name='save'),
    path('<int:pk>/share/', views.share_reel, name='share'),
    path('<int:pk>/comment/', views.add_comment, name='comment'),
    path('my/', views.my_reels, name='my_reels'),
    path('saved/', views.saved_reels, name='saved'),
]