from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def log_step(self, message: str):
        # Pytest shows these messages when the test is run with the -s option.
        print(f"[STEP] {message}", flush=True)

    def wait_for_visible(self, locator):
        locator.wait_for(state="visible")
        return locator

    def is_visible(self, locator):
        return locator.is_visible()
