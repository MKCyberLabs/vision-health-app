from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('file:///app/public/index.html')
        page.screenshot(path='screenshot.png', full_page=True)
        browser.close()

run()
