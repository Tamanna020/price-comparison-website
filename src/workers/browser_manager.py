"""Browser Isolation and Resource Management for PriceWise AI Beauty (Phase 6A).

Provides a safe, isolated, and resource-efficient Playwright Chromium browser manager:
1. Headless lifecycle management (clean start, isolated context, automatic teardown).
2. Navigation security: every URL is validated against the SecurityPolicy before navigation.
3. Resource blocking: images, media, and fonts are blocked to minimize CPU, memory, and bandwidth.
4. Navigation timeout enforcement: default 10s max wait time.
5. SSRF and private-network protection: prevents access to localhost, internal IPs, and cloud metadata.
"""

import logging
from typing import Generator, Optional
from contextlib import contextmanager

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright, Route, Error as PlaywrightError
from src.workers.security_policy import validate_browser_url

logger = logging.getLogger(__name__)

# Standard modern desktop User-Agent
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 PriceWiseAI/1.0"
)

# Resource types blocked by default to maximize speed and minimize memory/bandwidth
DEFAULT_BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}


class BrowserSecurityError(PermissionError):
    """Raised when an attempted navigation violates security navigation policy."""
    pass


class BrowserManager:
    """
    Manages Playwright browser lifecycle with security constraints and resource optimization.
    """

    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 10000,
        block_media: bool = True,
        user_agent: Optional[str] = None,
        blocked_resources: Optional[set[str]] = None,
    ):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.block_media = block_media
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.blocked_resources = blocked_resources or DEFAULT_BLOCKED_RESOURCE_TYPES

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._is_running: bool = False

    def start(self) -> "BrowserManager":
        """Start Playwright and launch the Chromium browser instance."""
        if self._is_running:
            return self

        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-sync",
                ],
            )
            self._is_running = True
            logger.info("Playwright Chromium browser started successfully.")
            return self
        except Exception as e:
            self.close()
            logger.error(f"Failed to launch Chromium browser: {e}")
            raise

    def close(self) -> None:
        """Close browser and stop Playwright cleanly without leaking processes."""
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self._browser = None

        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping Playwright: {e}")
            finally:
                self._playwright = None

        self._is_running = False
        logger.info("Playwright browser stopped cleanly.")

    def __enter__(self) -> "BrowserManager":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @property
    def is_running(self) -> bool:
        return self._is_running and self._browser is not None

    def new_context(self, **kwargs) -> BrowserContext:
        """
        Create a new isolated incognito browser context.
        Each context has independent cookies, cache, and session storage.
        """
        if not self.is_running or not self._browser:
            self.start()

        context_options = {
            "user_agent": self.user_agent,
            "viewport": {"width": 1280, "height": 800},
            "ignore_https_errors": False,
            "locale": "en-IN",
            "timezone_id": "Asia/Kolkata",
        }
        context_options.update(kwargs)

        context = self._browser.new_context(**context_options)
        context.set_default_timeout(self.timeout_ms)
        context.set_default_navigation_timeout(self.timeout_ms)
        return context

    def _setup_resource_blocking(self, page: Page) -> None:
        """Abort requests for media, images, and fonts to save memory and network bandwidth."""
        def route_handler(route: Route):
            req = route.request
            if req.resource_type in self.blocked_resources:
                try:
                    route.abort()
                except Exception:
                    pass
            else:
                try:
                    route.continue_()
                except Exception:
                    pass

        try:
            page.route("**/*", route_handler)
        except Exception as e:
            logger.warning(f"Failed to attach resource blocking route: {e}")

    def safe_navigate(
        self,
        page: Page,
        url: str,
        allow_test_urls: bool = False,
        wait_until: str = "domcontentloaded",
    ) -> bool:
        """
        Safely navigate to a URL after validating against the security navigation policy.
        
        Args:
            page: Playwright Page object.
            url: Target URL to navigate to.
            allow_test_urls: If True, allows 'about:blank' or 'data:text/html,...' for testing.
            wait_until: Navigation wait condition ('domcontentloaded', 'load', 'commit').

        Returns:
            bool: True if navigation succeeded.

        Raises:
            BrowserSecurityError: If URL violates the navigation security policy.
            PlaywrightError: If navigation fails or times out.
        """
        # Check test URLs if permitted
        is_test_url = url == "about:blank" or url.startswith("data:text/html")
        if allow_test_urls and is_test_url:
            page.goto(url, timeout=self.timeout_ms, wait_until=wait_until)
            return True

        # Validate against strict security policy
        is_valid, reason = validate_browser_url(url)
        if not is_valid:
            msg = f"Security Policy Violation: navigation to '{url}' blocked. Reason: {reason}"
            logger.error(msg)
            raise BrowserSecurityError(msg)

        # Navigate with strict timeout
        page.goto(url, timeout=self.timeout_ms, wait_until=wait_until)
        return True

    @contextmanager
    def page_session(self, allow_test_urls: bool = False) -> Generator[Page, None, None]:
        """
        Context manager for a single-use isolated Page session.
        Automatically destroys the context and page upon exit.
        """
        if not self.is_running:
            self.start()

        context = self.new_context()
        page = context.new_page()

        if self.block_media:
            self._setup_resource_blocking(page)

        try:
            yield page
        finally:
            try:
                page.close()
            except Exception:
                pass
            try:
                context.close()
            except Exception:
                pass

