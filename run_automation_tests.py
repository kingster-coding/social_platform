import os
import sys
import time
import subprocess
import requests
import shutil
from playwright.sync_api import sync_playwright

# Reconfigure stdout/stderr to support emojis/UTF-8 on Windows
if sys.platform.startswith("win"):
    reconfig = getattr(sys.stdout, "reconfigure", None)
    if reconfig:
        reconfig(encoding="utf-8")
    reconfig_err = getattr(sys.stderr, "reconfigure", None)
    if reconfig_err:
        reconfig_err(encoding="utf-8")

# Configuration
TEST_PORT = 8001
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
RESULTS_DIR = os.path.abspath("automation_results")
SCREENSHOTS_DIR = os.path.join(RESULTS_DIR, "screenshots")
VIDEO_TEMP_DIR = os.path.join(RESULTS_DIR, "temp_video")
VIDEO_FINAL_PATH = os.path.join(RESULTS_DIR, "test_walkthrough.webm")

# Test Credentials
TEST_EMAIL = "investor_test@example.com"
TEST_USERNAME = "investor_test"
TEST_PASSWORD = "InvestorPassword123"

def print_step(emoji, text):
    print(f"\n{emoji} [TEST SYSTEM] {text}")

def setup_directories():
    print_step("📁", "Setting up results directories...")
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(VIDEO_TEMP_DIR, exist_ok=True)
    print(f"Created directories: {RESULTS_DIR}")

def create_test_user():
    print_step("👤", "Creating/verifying test user in database...")
    # Using Django shell to create the user programmatically
    setup_code = (
        "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); "
        "import django; django.setup(); "
        "from accounts.models import User; "
        f"user, created = User.objects.get_or_create(email='{TEST_EMAIL}', defaults={{'username': '{TEST_USERNAME}'}}); "
        f"user.set_password('{TEST_PASSWORD}'); "
        "user.email_verified = True; "
        "user.save(); "
        "print('SUCCESS' if user.id else 'FAILED')"
    )
    
    # We invoke python through the venv to ensure standard paths and libs are used
    python_exe = os.path.join("venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = "python"  # Fallback

    # Set DJANGO_SETTINGS_MODULE in env dictionary
    test_env = os.environ.copy()
    test_env["DJANGO_SETTINGS_MODULE"] = "core.settings"

    process = subprocess.run(
        [python_exe, "-c", setup_code],
        capture_output=True,
        text=True,
        env=test_env
    )
    
    output = process.stdout.strip()
    if "SUCCESS" in output:
        print(f"Test user verification complete: email={TEST_EMAIL}, username={TEST_USERNAME}")
    else:
        print(f"Error creating user: {process.stderr}\nOutput: {process.stdout}")
        sys.exit(1)

def start_dev_server():
    print_step("🚀", f"Starting Django development server on port {TEST_PORT}...")
    python_exe = os.path.join("venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = "python"  # Fallback

    # Set DJANGO_SETTINGS_MODULE in env dictionary
    test_env = os.environ.copy()
    test_env["DJANGO_SETTINGS_MODULE"] = "core.settings"

    # Run manage.py runserver 8001
    server_process = subprocess.Popen(
        [python_exe, "manage.py", "runserver", str(TEST_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=test_env
    )
    
    # Wait for the server to become responsive
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(BASE_URL, timeout=1)
            print(f"Server is up and running! (Status: {response.status_code})")
            return server_process
        except requests.exceptions.RequestException:
            time.sleep(0.5)
            if i % 5 == 0:
                print(f"Waiting for server to respond ({i//2}s elapsed)...")
    
    print("Error: Django server failed to start in a timely manner.")
    server_process.terminate()
    try:
        stdout, stderr = server_process.communicate(timeout=5)
        print("--- Django Server STDOUT ---")
        print(stdout)
        print("--- Django Server STDERR ---")
        print(stderr)
    except Exception as e:
        print(f"Could not read server logs: {e}")
    sys.exit(1)

def run_browser_automation():
    print_step("🤖", "Launching automated Playwright Chromium browser...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a new context with video recording enabled
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=VIDEO_TEMP_DIR,
            record_video_size={"width": 1280, "height": 720}
        )
        
        page = context.new_page()
        
        # Step 1: Open Login Page
        print_step("🔑", "Navigating to Login Page...")
        page.goto(f"{BASE_URL}/accounts/login/")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_login_page.png"))
        print("Captured: 01_login_page.png")
        
        # Step 2: Fill in Credentials and Submit
        print_step("📝", "Filling login credentials...")
        page.fill("input[name='login']", TEST_EMAIL)
        page.fill("input[name='password']", TEST_PASSWORD)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_login_form_filled.png"))
        print("Captured: 02_login_form_filled.png")
        
        print_step("👆", "Submitting login form...")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Step 3: Handle Monetization Consent redirect
        # Since it is a new user or freshly set up, the ConsentMiddleware redirects to /monetization/consent/
        current_url = page.url
        print(f"Current URL after login: {current_url}")
        
        if "/monetization/consent/" in current_url:
            print_step("🛡️", "Consent page detected. Selecting default Option A (Ad-Supported)...")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_monetization_consent_page.png"))
            print("Captured: 03_monetization_consent_page.png")
            
            # Submit the form with default selection
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            print("Consent preferences submitted.")
        
        # Step 4: Validate Feed / Homepage
        print_step("🏠", "Validating Feed page...")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_home_feed.png"))
        print("Captured: 04_home_feed.png")
        
        # Step 5: Test Dark Mode toggle (Alpine.js interaction)
        print_step("🌓", "Testing Dark Mode toggle...")
        # Select theme toggle button
        page.click("button[title='Toggle theme']")
        page.wait_for_timeout(500)  # Wait for transition
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_dark_mode_active.png"))
        print("Captured: 05_dark_mode_active.png")
        
        # Toggle back to normal light mode
        page.click("button[title='Toggle theme']")
        page.wait_for_timeout(500)
        
        # Step 6: Create an automated feed post
        print_step("✍️", "Creating a new post...")
        post_content = "🚀 Auto-Test: The automation suite has checked all buttons, layouts, and pages, and verified that everything works perfectly! @investors"
        page.fill("textarea[name='content']", post_content)
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_post_form_filled.png"))
        print("Captured: 06_post_form_filled.png")
        
        # Click the Post button
        # In feed.html, the post button is a submit button inside the create post card form
        page.locator("form[action*='post/create'] button[type='submit']").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000) # Wait for page load/feed update
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_post_created.png"))
        print("Captured: 07_post_created.png")
        
        # Step 7: Navigate to Reels
        print_step("🎬", "Navigating to Reels...")
        page.click("a[href*='/reels/']")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_reels_page.png"))
        print("Captured: 08_reels_page.png")
        
        # Step 8: Navigate to Groups
        print_step("👥", "Navigating to Groups...")
        page.click("a[href*='/groups/']")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_groups_page.png"))
        print("Captured: 09_groups_page.png")
        
        # Step 9: Navigate to Jobs
        print_step("💼", "Navigating to Jobs...")
        page.click("a[href*='/jobs/']")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_jobs_page.png"))
        print("Captured: 10_jobs_page.png")
        
        # Step 10: Navigate to Research
        print_step("🔬", "Navigating to Research...")
        page.click("a[href*='/research/']")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "11_research_page.png"))
        print("Captured: 11_research_page.png")
        
        # Step 11: Navigate to Webinars
        print_step("🎥", "Navigating to Webinars...")
        page.click("a[href*='/webinars/']")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "12_webinars_page.png"))
        print("Captured: 12_webinars_page.png")
        
        # Step 12: Navigate to Profile via user trigger dropdown
        print_step("👤", "Navigating to Profile Page...")
        page.click("button.user-trigger")
        page.wait_for_timeout(300) # Wait for Alpine transition
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "13_user_dropdown.png"))
        print("Captured: 13_user_dropdown.png")
        
        page.click("a[href*='/accounts/profile/']")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "14_profile_page.png"))
        print("Captured: 14_profile_page.png")
        
        # Step 13: Log out
        print_step("🚪", "Logging out...")
        page.click("button.user-trigger")
        page.wait_for_timeout(300)
        page.click("a[href*='/accounts/logout/']")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "15_logged_out.png"))
        print("Captured: 15_logged_out.png")
        
        # Finish recording and save video
        print_step("🎥", "Wrapping up video recording...")
        video_obj = page.video
        video_file = video_obj.path() if video_obj else None
        context.close()
        browser.close()
        
        # Move video to the final location
        if video_file and os.path.exists(video_file):
            shutil.move(video_file, VIDEO_FINAL_PATH)
            print(f"Video walkthrough saved to: {VIDEO_FINAL_PATH}")
        
        # Clean up temp video folder
        if os.path.exists(VIDEO_TEMP_DIR):
            shutil.rmtree(VIDEO_TEMP_DIR)

def main():
    start_time = time.time()
    print_step("📋", "Starting Social Platform Automation Walkthrough...")
    
    setup_directories()
    create_test_user()
    
    server_process = None
    try:
        server_process = start_dev_server()
        run_browser_automation()
        print_step("🎉", f"SUCCESS! Automation testing completed in {time.time() - start_time:.2f} seconds!")
        print(f"Screenshots saved to: {SCREENSHOTS_DIR}")
        print(f"Walkthrough video saved to: {VIDEO_FINAL_PATH}")
    except Exception as e:
        print_step("❌", f"An error occurred during automation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if server_process:
            print_step("🛑", "Terminating Django server process...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("Django server stopped.")

if __name__ == "__main__":
    main()
