"""
WHAT: URL patterns for feed app
WHY: Feed pages ke URLs define karne ke liye
"""

from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [
    # Main feed
    path('', views.feed, name='feed'),
    
    # Posts
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    
    # Interactions
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:pk>/comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    path('post/<int:pk>/share/', views.share_post, name='share_post'),
    path('post/<int:pk>/save/', views.save_post, name='save_post'),
    path('hashtag/<str:tag>/', views.hashtag_posts, name='hashtag'),
    path('api/trending-hashtags/', views.trending_hashtags, name='trending_hashtags'),
    
    # Saved posts
    path('saved/', views.saved_posts, name='saved_posts'),
    
    # Stories
    path('story/create/', views.create_story, name='create_story'),
]