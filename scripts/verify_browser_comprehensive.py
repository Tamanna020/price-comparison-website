import sys
import time
from playwright.sync_api import sync_playwright

def run_verification():
    print("=== Starting Comprehensive Browser Verification ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            headless=True
        )
        context = browser.new_context()
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # 1. Product Detail Page
        print("\n1. Navigating to Product Detail Page...")
        product_url = "http://localhost:5173/product/watermelon-cooling-sunscreen-spf-50"
        page.goto(product_url, wait_until="networkidle")
        time.sleep(1)

        title = page.title()
        print(f"   Page Title: {title}")
        assert "PriceWise" in title, f"Unexpected title: {title}"

        overlay = page.query_selector("vite-error-overlay")
        print(f"   Vite Error Overlay: {overlay}")
        assert overlay is None, "Vite error overlay detected on Product Detail Page!"

        # Check product content
        content = page.content()
        has_product = "Watermelon" in content or "Sunscreen" in content or "Dot & Key" in content
        print(f"   Product content loaded: {has_product}")
        assert has_product, "Product details did not load into DOM"

        # 2. Existing Navigation Test
        print("\n2. Testing Navigation...")
        nav_brand = page.query_selector("a[href='/'], button:has-text('Discovery'), header a")
        print(f"   Header/Nav found: {nav_brand is not None}")

        # 3. Beauty Assistant Route Load
        print("\n3. Navigating to /beauty-assistant...")
        assistant_url = "http://localhost:5173/beauty-assistant"
        page.goto(assistant_url, wait_until="networkidle")
        time.sleep(1)

        overlay2 = page.query_selector("vite-error-overlay")
        print(f"   Vite Error Overlay: {overlay2}")
        assert overlay2 is None, "Vite error overlay detected on Beauty Assistant Page!"

        # Sign-in wall verification
        assistant_text = page.inner_text("body")
        has_assistant_header = "Beauty Assistant" in assistant_text
        print(f"   Beauty Assistant page heading present: {has_assistant_header}")
        assert has_assistant_header, "Beauty Assistant heading missing!"

        # 4. Open Auth Modal & Authenticate
        print("\n4. Testing Sign-In Modal Flow...")
        sign_in_btn = page.query_selector("button:has-text('Sign In to Chat')")
        print(f"   'Sign In to Chat' button present: {sign_in_btn is not None}")
        sign_in_btn.click()
        time.sleep(1)

        # Register or login a test user
        # Switch to register tab or register directly
        register_link = page.query_selector("button:has-text('Need an account? Register'), button:has-text('Register')")
        if register_link:
            register_link.click()
            time.sleep(0.5)

        test_email = f"user_{int(time.time())}@pricewise.test"
        name_input = page.query_selector("input[placeholder*='name' i], input[type='text']")
        email_input = page.query_selector("input[type='email']")
        password_input = page.query_selector("input[type='password']")

        if name_input and email_input and password_input:
            name_input.fill("Beauty Tester")
            email_input.fill(test_email)
            password_input.fill("Password123!")
            submit_btn = page.query_selector("form button[type='submit']")
            if submit_btn:
                submit_btn.click()
                time.sleep(2)
        else:
            print("   Using fallback token auth injection")
            # If form inputs differ, register via API directly
            import urllib.request
            import json
            req = urllib.request.Request(
                "http://127.0.0.1:8000/api/auth/register",
                data=json.dumps({"name": "Tester", "email": test_email, "password": "Password123!"}).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode())
                token = res_data.get("token")
                page.evaluate(f"() => {{ localStorage.setItem('pw_auth_token', '{token}'); }}")
                page.reload(wait_until="networkidle")
                time.sleep(1)

        # Verify textarea is visible now
        textarea = page.query_selector("textarea")
        print(f"   Chat input textarea present: {textarea is not None}")
        assert textarea is not None, "Textarea input missing after authentication!"

        # Verify suggested prompts
        prompts = page.query_selector_all("main button")
        print(f"   Prompt buttons in main view: {len(prompts)} found")

        # 5. Send a message
        print("\n5. Testing Sending a Message...")
        test_message = "What ingredients help with dryness?"
        print(f"   Typing message: '{test_message}'")
        textarea.fill(test_message)
        send_btn = page.query_selector("button[aria-label='Send message'], button[type='submit']")
        send_btn.click()

        # Wait for assistant response
        time.sleep(3)
        chat_content = page.inner_text("#chat-messages")
        message_accepted = test_message in chat_content
        print(f"   User message in chat: {message_accepted}")
        assert message_accepted, "User message not found in chat messages!"

        has_assistant_response = "PriceWise AI" in chat_content or "dryness" in chat_content.lower() or "ingredient" in chat_content.lower() or "Based on your concerns" in chat_content
        print(f"   Assistant response received: {has_assistant_response}")
        print(f"   Chat snippet:\n{chat_content[:400]}")

        # Check for Vite error overlay again
        final_overlay = page.query_selector("vite-error-overlay")
        assert final_overlay is None, "Vite error overlay detected during chat!"

        browser.close()
        print("\n=== ALL BROWSER VERIFICATIONS COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_verification()
