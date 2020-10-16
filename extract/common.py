import re
import lxml
import urllib.parse as urlparse
from urllib.parse import parse_qs
import tempfile
import textract
import warnings
import scrapelib
from .utils import (
    pdfdata_to_text,
    text_after_line_numbers,
    text_before_line_numbers,
    text_from_element_lxml,
    text_from_element_xpath,
    text_from_element_siblings_lxml,
    text_from_element_siblings_xpath,
    clean,
    get_filename,
)

global SCRAPER
SCRAPER = scrapelib.Scraper(verify=False)
SCRAPER.user_agent = "Mozilla"
warnings.filterwarnings("ignore", module="urllib3")

# disable SSL validation and ignore warnings


def extract_simple_pdf(data, metadata, **kwargs):
    return pdfdata_to_text(data)


def extract_line_numbered_pdf(data, metadata, **kwargs):
    return text_after_line_numbers(pdfdata_to_text(data))


def extract_line_post_numbered_pdf(data, metadata, **kwargs):
    return text_before_line_numbers(pdfdata_to_text(data))


def extract_ca_sometimes_numbered_pdf(data, metadata, **kwargs):
    """
    A few states have bills both with numbered lines and without.
    In these cases, we need to look at the start of the lines
    to determine which extraction function to use.

    In addition, CA requires an extra route call in order to get the actual PDF.
    This is done by getting a session token and making a new request.
    """

    write_to_file = kwargs.get("write_to_file")

    # Data is the first CA HTML request content
    # metadata is the version
    # get and parse the initial CA page
    doc = lxml.html.fromstring(data)
    parsed = urlparse.urlparse(metadata["url"])
    bill_id = parse_qs(parsed.query)["bill_id"][0]
    bill_version = parse_qs(parsed.query)["version"][0]

    # Get pdf_link2, view_state, and other params
    pdf_link = doc.get_element_by_id("pdf_link2").name
    view_state = doc.get_element_by_id("j_id1:javax.faces.ViewState:0").value
    download_form_obj = doc.get_element_by_id("downloadForm")
    download_form_action = download_form_obj.action
    base_url = "https://leginfo.legislature.ca.gov"

    # Construct the second request body and headers
    req_body = {
        "downloadForm": "downloadForm",
        "javax.faces.ViewState": view_state,
        "pdf_link2": pdf_link,
        "bill_id": bill_id,
        "version": bill_version,
    }

    second_req_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    }

    metadata["url"] = base_url + download_form_action
    # Send request and save second request as temp.pdf
    ca_content = SCRAPER.post(metadata["url"], data=req_body, headers=second_req_headers)

    if write_to_file:
        raw_filename = get_filename(metadata)
        with open(raw_filename, "wb") as f:
            f.write(ca_content.content)

    return extract_sometimes_numbered_pdf(ca_content.content, metadata)


def extract_sometimes_numbered_pdf(data, metadata, **kwargs):
    """
    A few states have bills both with numbered lines and without.
    In these cases, we need to look at the start of the lines
    to determine which extraction function to use.
    """

    pdf_text = pdfdata_to_text(data)
    lines = pdf_text.split("\n")

    # Looking for lines that begin with a number
    pattern = re.compile(r"^\s*\d+\s+(.*)", flags=re.MULTILINE)
    number_of_numbered_lines = pattern.findall(pdf_text)

    # If more than 10% of the text begins with numbers, then we are
    # probably looking at a bill with numbered lines.
    THRESHOLD_NUMBERED_PDF = 0.10

    ratio_of_numbered_lines = len(number_of_numbered_lines) / len(lines)

    if ratio_of_numbered_lines > THRESHOLD_NUMBERED_PDF:
        return extract_line_numbered_pdf(data, metadata)
    else:
        return extract_simple_pdf(data, metadata)


def extract_pre_tag_html(data, metadata, **kwargs):
    """
    Many states that provide bill text on HTML webpages (e.g. AK, FL)
    have the text inside <pre> tags (for preformatted text).
    """

    text_inside_matching_tag = text_from_element_lxml(data, ".//pre")
    return text_after_line_numbers(text_inside_matching_tag)


def extract_from_p_tags_html(data, metadata, **kwargs):
    """
    For a few states providing bill text in HTML, we just want to get all
    the text in paragraph tags on the page. There may be several paragraphs.
    """

    text = text_from_element_siblings_lxml(data, ".//p")
    return text


def extractor_for_elements_by_class(bill_text_element_class):
    return extractor_for_element_by_selector(".//div[@class='" + bill_text_element_class + "']")


def extractor_for_element_by_id(bill_text_element_id):
    return extractor_for_element_by_selector(".//div[@id='" + bill_text_element_id + "']")


def extractor_for_element_by_selector(bill_text_element_selector):
    def _my_extractor(data, metadata, **kwargs):
        text_inside_matching_tag = text_from_element_lxml(data, bill_text_element_selector)
        return clean(text_inside_matching_tag)

    return _my_extractor


def extractor_for_element_by_xpath(bill_text_element_selector):
    def _my_extractor(data, metadata, **kwargs):
        text_inside_matching_tag = text_from_element_xpath(data, bill_text_element_selector)
        return clean(text_inside_matching_tag)

    return _my_extractor


def extractor_for_elements_by_xpath(bill_text_element_selector):
    def _my_extractor(data, metadata, **kwargs):
        text_inside_matching_tag = text_from_element_siblings_xpath(
            data, bill_text_element_selector
        )
        return clean(text_inside_matching_tag)

    return _my_extractor


def textract_extractor(**kwargss):
    """ pass through kwargss to textextract.process """
    assert "extension" in kwargss, "Must supply extension"

    def func(data, metadata, **kwargs):
        with tempfile.NamedTemporaryFile(delete=False) as tmpf:
            tmpf.write(data)
            tmpf.flush()
            return textract.process(tmpf.name, **kwargss).decode()

    return func


def extract_from_code_tags_html(data, metadata, **kwargs):
    """
    Some states (e.g. IL) have the bill text inside
    <code> tags (as it renders as fixed-width).
    """

    text = text_from_element_siblings_lxml(data, ".//code")
    return text
