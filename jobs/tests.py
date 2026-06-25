from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Company, Job, JobApplication, SavedJob, JobCategory
from monetization.models import UserConsent

User = get_user_model()


class JobsAppTests(TestCase):
    """
    WHAT: Automated integration and unit tests for Jobs app
    """

    def setUp(self):
        # Create users
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@company.com',
            password='Password123'
        )
        self.seeker = User.objects.create_user(
            username='seeker',
            email='seeker@career.com',
            password='Password123'
        )
        
        # Create consent to bypass ConsentMiddleware
        UserConsent.objects.create(user=self.recruiter, consent_type='ads')
        UserConsent.objects.create(user=self.seeker, consent_type='ads')
        
        # Create a company profile owned by recruiter
        self.company = Company.objects.create(
            name="Google DeepMind Labs",
            slug="deepmind-labs",
            description="Deep artificial intelligence research",
            industry="Technology",
            size="1000+",
            owner=self.recruiter
        )
        
        # Create a category
        self.category = JobCategory.objects.create(
            name="AI Research",
            slug="ai-research"
        )
        
        # Create a job listing
        self.job = Job.objects.create(
            title="Senior AI Researcher",
            company=self.company,
            category=self.category,
            description="Build agentic systems",
            requirements="Python, PyTorch",
            responsibilities="Design RL algorithms",
            job_type="full_time",
            experience_level="senior",
            location_type="remote",
            location="London, UK",
            status="active"
        )

    def test_post_job_view(self):
        """Verify recruiter can post jobs for their company"""
        self.client.login(email='recruiter@company.com', password='Password123')
        
        # Count original jobs
        orig_count = Job.objects.count()
        
        response = self.client.post(
            reverse('jobs:post_job_company', kwargs={'company_id': self.company.pk}),
            {
                'title': 'Research Engineer',
                'category': self.category.pk,
                'description': 'Tuning large models',
                'requirements': 'Coding',
                'responsibilities': 'Building infra',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'location_type': 'onsite',
                'location': 'London, UK',
                'status': 'active',
                'salary_currency': 'INR',
                'salary_period': 'yearly',
                'vacancies': 1
            },
            follow=True
        )
        self.assertEqual(Job.objects.count(), orig_count + 1)

    def test_apply_to_job(self):
        """Verify job seeker can apply to a job with PDF upload"""
        self.client.login(email='seeker@career.com', password='Password123')
        
        mock_pdf = SimpleUploadedFile("resume.pdf", b"pdf_data_bytes", content_type="application/pdf")
        
        response = self.client.post(
            reverse('jobs:apply', kwargs={'pk': self.job.pk}),
            {
                'resume': mock_pdf,
                'cover_letter': 'I love DeepMind and agentic systems!'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(JobApplication.objects.filter(job=self.job, applicant=self.seeker).count(), 1)

    def test_recruiter_can_update_status_and_notify(self):
        """Verify recruiter can update application status and notification triggers"""
        # Create application first
        mock_pdf = SimpleUploadedFile("resume.pdf", b"pdf_data_bytes", content_type="application/pdf")
        application = JobApplication.objects.create(
            job=self.job,
            applicant=self.seeker,
            resume=mock_pdf,
            applicant_name="Seeker User",
            applicant_email="seeker@career.com"
        )
        
        # Log in as recruiter to update status
        self.client.login(email='recruiter@company.com', password='Password123')
        
        response = self.client.post(
            reverse('jobs:update_status', kwargs={'app_id': application.pk}),
            {'status': 'shortlisted'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify status updated
        application.refresh_from_db()
        self.assertEqual(application.status, 'shortlisted')
        
        # Verify user received a real-time notification
        from user_notifications.models import UserNotification
        self.assertEqual(
            UserNotification.objects.filter(
                recipient=self.seeker, 
                notification_type='job_status'
            ).count(), 
            1
        )

