"""
WHAT: URL patterns for research app
"""

from django.urls import path
from . import views

app_name = 'research'

urlpatterns = [
    path('', views.paper_list, name='paper_list'),
    path('upload/', views.upload_paper, name='upload'),
    path('paper/<int:pk>/', views.paper_detail, name='paper_detail'),
    path('paper/<int:pk>/download/', views.download_paper, name='download'),
    path('paper/<int:pk>/like/', views.like_paper, name='like'),
    path('paper/<int:pk>/save/', views.save_paper, name='save'),
    path('paper/<int:pk>/comment/', views.add_comment, name='comment'),
    path('researcher/<str:username>/follow/', views.follow_researcher, name='follow'),
    path('library/', views.my_library, name='library'),
]