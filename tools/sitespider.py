import requests
from urllib.parse import urljoin, urlparse
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from google.cloud import storage
from restaurantagent.tools.vertexai import call_gemini
from bs4 import BeautifulSoup
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_menu(url: str)->str:
    """
    Finds the menu present in the website in webpage or images.
    

    Args:
        url (str): The URL of the website to spider.

    Returns:
        Menu item found in the website along with menu item url.
    """
    logger.info(f"Finding internal links for URL: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return f"An error occurred while fetching {url}: {e}"

    soup = BeautifulSoup(response.content, 'html.parser')
    internal_links = set()
    domain_name = urlparse(url).netloc

    for a_tag in soup.find_all('a', href=True):
        href = a_tag.attrs['href']
        # Join the URL with the href to handle relative links
        full_url = urljoin(url, href)
        # Parse the full URL to get the domain name
        href_domain = urlparse(full_url).netloc

        if href_domain == domain_name:
            internal_links.add(full_url)

    logger.info(f"Found {len(internal_links)} internal links for {url}.")

    #get menu items
    menulink=""
    menuimages=[]
    menuitems=""
    for link in internal_links:
        mitems,mlink=get_webpage_text(link)
        menulink+=mlink
        menuitems+=mitems
        
    return menuitems+"\n"+menulink

def get_webpage_text(url: str):
    """
    Downloads a webpage and returns its text content.

    Args:
        url (str): The URL of the webpage to download.

    Returns:
        str: The text content of the webpage.
    """
    logger.info(f"Getting webpage text/menu for URL: {url}")
    prompt = "does this content contain restaurant menu items? please only respond with yes or no"
    
    if url.lower().endswith('.pdf'):
        mimetype = 'application/pdf'
    elif url.lower().endswith('.jpg'):
        mimetype = 'image/jpeg'
    elif url.lower().endswith('.png'):
        mimetype = 'image/png'
    else:
        mimetype = 'text/plain'
        
    has_menu = call_gemini(prompt=prompt, url=url, mimetype=mimetype)
    logger.info(f"Initial menu check for {url} returned: '{has_menu}'")
    
    if "no" in has_menu.lower():
        logger.info(f"No menu found on {url} based on initial check. Returning empty string.")
        return "",""
    else:
        logger.info(f"Menu content detected on {url}. Proceeding to extract items.")
        prompt = "please return a list of menu items and their prices from the url"
        menu_items = call_gemini(prompt=prompt, url=url, mimetype=mimetype)
        logger.info(f"Extracted menu items from {url}: {menu_items[:250]}...")
        return menu_items,url

def save_screenshot_to_gcs(url: str, bucket_name: str):
    """
    Renders a URL in a headless browser, saves a full-page screenshot to a GCS bucket,
    and returns the GCS URL of the saved image.

    Args:
        url (str): The URL to take a screenshot of.
        bucket_name (str): The name of the Google Cloud Storage bucket.

    Returns:
        str: The GCS URL of the saved image (e.g., gs://bucket/savedimage.jpg).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle")
            screenshot_filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_filename, full_page=True)

            # Upload to GCS
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(screenshot_filename)
            blob.upload_from_filename(screenshot_filename)

            # Clean up the temporary file
            os.remove(screenshot_filename)

            return f"gs://{bucket_name}/{screenshot_filename}"
        finally:
            browser.close()