import re
import requests
from bs4 import BeautifulSoup
import validators
import ssl
import logging


class URLValidator:
    def __init__(self, url):
        self.url = url

    def is_valid_format(self):
        return self._is_valid_url(self.url) and validators.url(self.url)

    def get_status_code(self):
        try:
            response = requests.get(self.url, timeout=5)
            return response.status_code, response.text
        except requests.exceptions.Timeout:
            return "Request Timeout", None
        except requests.exceptions.TooManyRedirects:
            return "Too Many Redirects", None
        except requests.exceptions.RequestException as e:
            return f"Request Exception: {e}", None

    def is_https(self):
        return self.url.startswith('https://')

    def extract_page_info(self):
        status_code, content = self.get_status_code()
        if status_code != 200:
            return f"Error: Status code {status_code}"

        soup = BeautifulSoup(content, 'html.parser')
        title = soup.title.string if soup.title else "No Title"
        description = soup.find('meta', attrs={'name': 'description'})
        description_content = description['content'] if description else "No Description"
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords_content = keywords['content'] if keywords else "No Keywords"
        internal_links = [a['href'] for a in soup.find_all(
            'a', href=True) if a['href'].startswith('/')]
        external_links = [a['href'] for a in soup.find_all(
            'a', href=True) if not a['href'].startswith('/')]

        headings = {
            'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
            'h2': [h.get_text(strip=True) for h in soup.find_all('h2')],
            'h3': [h.get_text(strip=True) for h in soup.find_all('h3')],
            'h4': [h.get_text(strip=True) for h in soup.find_all('h4')],
            'h5': [h.get_text(strip=True) for h in soup.find_all('h5')],
            'h6': [h.get_text(strip=True) for h in soup.find_all('h6')],
        }

        images = soup.find_all('img')
        alt_tags = [img['alt'] for img in images if 'alt' in img.attrs]

        text = soup.get_text()
        text_length = len(text)
        html_length = len(content)
        text_to_html_ratio = text_length / html_length if html_length > 0 else 0

        page_load_time = self._measure_page_load_time()

        mobile_friendly = self._is_mobile_friendly(soup)

        return {
            'title': title,
            'description': description_content,
            'keywords': keywords_content,
            'internal_links': internal_links,
            'external_links': external_links,
            'headings': headings,
            'alt_tags': alt_tags,
            'text_to_html_ratio': text_to_html_ratio,
            'page_load_time': page_load_time,
            'mobile_friendly': mobile_friendly,
        }

    def check_ssl_certificate(self):
        if not self.is_https():
            return "No SSL Certificate for non-HTTPS URLs"

        try:
            cert = ssl.get_server_certificate(
                (self.url.replace('https://', ''), 443))
            return cert
        except Exception as e:
            return f"SSL Certificate Error: {e}"

    def _is_valid_url(self, url):
        regex = re.compile(
            r'^(https?|ftp)://',  # http://, https://, or ftp://
            re.IGNORECASE
        )
        return re.match(regex, url) is not None

    def _seo_analysis(self, title, description, keywords, headings, alt_tags, text_to_html_ratio, page_load_time,
                      mobile_friendly, internal_links, external_links):
        score = 0

        # Title analysis
        if title and len(title) <= 60:
            score += 10
        elif title:
            score += 5  # partial credit for having a title

        # Meta description analysis
        if description and 150 <= len(description) <= 160:
            score += 10
        elif description:
            score += 5  # partial credit for having a description

        # Keywords analysis
        if keywords:
            score += 10

        # Headings analysis
        if headings['h1']:
            score += 10
        if headings['h2']:
            score += 5  # additional score for h2 presence

        # Internal and external links analysis
        if internal_links:
            score += 10
        if external_links:
            score += 10

        # Alt tags for images
        if alt_tags:
            score += 10

        # Text to HTML ratio
        if text_to_html_ratio > 0.1:
            score += 10

        # Page load time analysis
        if page_load_time < 3:
            score += 10
        elif page_load_time < 5:
            score += 5  # partial credit for acceptable load time

        # Mobile friendly analysis
        if mobile_friendly:
            score += 10

        return score

    def _measure_page_load_time(self):
        try:
            response = requests.get(self.url, timeout=5)
            return response.elapsed.total_seconds()
        except requests.exceptions.RequestException:
            return float('inf')  # return a very high value to indicate failure

    def _is_mobile_friendly(self, soup):
        meta_viewport = soup.find('meta', attrs={'name': 'viewport'})
        return bool(meta_viewport)


def setup_logging():
    logging.basicConfig(filename='url_validator.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def log_results(url, status_code, https_check, ssl_info, page_info):
    logging.info(f"URL: {url}")
    logging.info(f"Status Code: {status_code}")
    logging.info(f"HTTPS Check: {'Yes' if https_check else 'No'}")
    logging.info(f"SSL Certificate: {ssl_info}")
    logging.info(f"Title: {page_info['title']}")
    logging.info(f"Description: {page_info['description']}")
    logging.info(f"Keywords: {page_info['keywords']}")
    logging.info(f"Internal Links: {page_info['internal_links']}")
    logging.info(f"External Links: {page_info['external_links']}")
    logging.info(f"Headings: {page_info['headings']}")
    logging.info(f"Alt Tags: {page_info['alt_tags']}")
    logging.info(f"Text to HTML Ratio: {page_info['text_to_html_ratio']}")
    logging.info(f"Page Load Time: {page_info['page_load_time']}")
    logging.info(f"Mobile Friendly: {
                 'Yes' if page_info['mobile_friendly'] else 'No'}")


def main(url):
    validator = URLValidator(url)
    setup_logging()

    if validator.is_valid_format():
        status_code, _ = validator.get_status_code()
        https_check = validator.is_https()
        page_info = validator.extract_page_info()
        ssl_info = validator.check_ssl_certificate()

        if isinstance(status_code, int):
            print(f"URL is valid and returned status code: {status_code}")
            print(f"HTTPS Check: {'Yes' if https_check else 'No'}")
            print(f"SSL Certificate: {ssl_info}")
            print("Page Info:")
            print(f"Title: {page_info['title']}")
            print(f"Description: {page_info['description']}")
            print(f"Keywords: {page_info['keywords']}")
            print(f"Internal Links: {page_info['internal_links']}")
            print(f"External Links: {page_info['external_links']}")
            print(f"Headings: {page_info['headings']}")
            print(f"Alt Tags: {page_info['alt_tags']}")
            print(f"Text to HTML Ratio: {page_info['text_to_html_ratio']}")
            print(f"Page Load Time: {page_info['page_load_time']}")
            print(f"Mobile Friendly: {
                  'Yes' if page_info['mobile_friendly'] else 'No'}")

            seo_score = validator._seo_analysis(page_info['title'], page_info['description'], page_info['keywords'],
                                                page_info['headings'], page_info['alt_tags'], page_info['text_to_html_ratio'],
                                                page_info['page_load_time'], page_info['mobile_friendly'],
                                                page_info['internal_links'], page_info['external_links'])
            print(f"SEO Score: {seo_score}")

            log_results(url, status_code, https_check, ssl_info, page_info)
        else:
            print(f"Error: {status_code}")
    else:
        print("URL format is invalid.")


if __name__ == "__main__":
    url = "https://github.com/"
    main(url)
