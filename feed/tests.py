from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from .models import Post, Like, Comment, Story
from monetization.models import UserConsent

User = get_user_model()


class FeedAppTests(TestCase):
    """
    WHAT: Automated integration and unit tests for Feed App
    WHY: Verify feed, posts, comments, likes, and stories work perfectly
    """

    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@social.com',
            password='Password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@social.com',
            password='Password123'
        )
        
        # Create consent to bypass ConsentMiddleware
        UserConsent.objects.create(user=self.user1, consent_type='ads')
        UserConsent.objects.create(user=self.user2, consent_type='ads')
        
        # Create a post for user1
        self.post = Post.objects.create(
            author=self.user1,
            content="Hello world #testing #demo",
            privacy="public"
        )

    def test_feed_view_requires_login(self):
        """Verify redirect to login for unauthenticated users"""
        response = self.client.get(reverse('feed:feed'))
        self.assertNotEqual(response.status_code, 200)

    def test_authenticated_user_can_view_feed(self):
        """Verify logged in user can access home feed"""
        self.client.login(email='user1@social.com', password='Password123')
        response = self.client.get(reverse('feed:feed'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world")

    def test_post_creation(self):
        """Verify users can submit a post"""
        self.client.login(email='user1@social.com', password='Password123')
        response = self.client.post(
            reverse('feed:create_post'),
            {'content': 'Test post creation content', 'privacy': 'public'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(content='Test post creation content').exists())

    def test_like_post_toggle(self):
        """Verify liking and unliking a post (including HTMX response)"""
        self.client.login(email='user2@social.com', password='Password123')
        
        # Like post
        response = self.client.post(
            reverse('feed:like_post', kwargs={'pk': self.post.pk}),
            {'reaction': 'like'}
        )
        self.assertEqual(Like.objects.filter(user=self.user2, post=self.post).count(), 1)
        
        # Unlike post
        response = self.client.post(
            reverse('feed:like_post', kwargs={'pk': self.post.pk}),
            {'reaction': 'like'}
        )
        self.assertEqual(Like.objects.filter(user=self.user2, post=self.post).count(), 0)

    def test_add_comment(self):
        """Verify users can comment on posts"""
        self.client.login(email='user2@social.com', password='Password123')
        response = self.client.post(
            reverse('feed:add_comment', kwargs={'pk': self.post.pk}),
            {'content': 'Great post!'},
            follow=True
        )
        self.assertEqual(Comment.objects.filter(user=self.user2, post=self.post, content='Great post!').count(), 1)

    def test_create_story(self):
        """Verify user can share a story"""
        self.client.login(email='user1@social.com', password='Password123')
        
        # Create small mock text file or image for upload
        from django.core.files.uploadedfile import SimpleUploadedFile
        mock_file = SimpleUploadedFile("story.jpg", b"file_content", content_type="image/jpeg")
        
        response = self.client.post(
            reverse('feed:create_story'),
            {'image': mock_file},
            follow=True
        )
        self.assertEqual(Story.objects.filter(author=self.user1).count(), 1)
        story = Story.objects.get(author=self.user1)
        self.assertTrue(story.is_active)

