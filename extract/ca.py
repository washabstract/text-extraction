import os
import re
import time
import urllib.parse as urlparse
from urllib.parse import parse_qs

import click
import lxml
import requests

from .common import extract_sometimes_numbered_pdf
from .utils import jid_to_abbr


MIMETYPES = {
    "application/pdf": "pdf",
    "text/html": "html",
    "application/msword": "doc",
    "application/rtf": "rtf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/xml": "html",
}


def get_pdf_from_link(link, data=None, metadata=None, fail=False):
    base_url = "https://leginfo.legislature.ca.gov"
    link_parsed = urlparse.urlparse(link)
    link_queries = parse_qs(link_parsed.query)
    url_parsed = url_queries = None
    if metadata and "url" in metadata:
        url_parsed = urlparse.urlparse(metadata["url"])
        url_queries = parse_qs(url_parsed.query)
    bill_id = bill_version = None
    if link_queries and "bill_id" in link_queries and "version" in link_queries:
        bill_id = link_queries["bill_id"][0]
        bill_version = link_queries["version"][0]
    elif url_queries and "bill_id" in url_queries and "version" in url_queries:
        bill_id = url_queries["bill_id"][0]
        bill_version = url_queries["verison"][0]
    elif metadata and "bill_id" in metadata and "bill_version" in metadata:
        bill_id = metadata["bill_id"]
        bill_version = metadata["bill_version"]

    if not bill_id or not bill_version:
        return None, metadata

    doc = None
    if data:
        doc = lxml.html.fromstring(data)
    else:
        if metadata:
            url = metadata["url"]
        else:
            url = link
        new_request = requests.get(url)
        doc = lxml.html.fromstring(new_request.content)

    pdf_link = doc.get_element_by_id("pdf_link2").name
    view_state = doc.get_element_by_id("j_id1:javax.faces.ViewState:0").value
    download_form_action = doc.get_element_by_id("downloadForm").action

    # Construct the second request body and headers
    req_body = {
        "downloadForm": "downloadForm",
        "javax.faces.ViewState": view_state,
        "pdf_link2": pdf_link,
        "bill_id": bill_id,
        "version": bill_version,
    }

    req_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:87.0) Gecko/20100101 Firefox/87.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    }

    if metadata:
        metadata["url"] = base_url + download_form_action
        ca_content = requests.post(metadata["url"], data=req_body, headers=req_headers)
    else:
        link = base_url + download_form_action
        ca_content = requests.post(link, data=req_body, headers=req_headers)
    attempts = 0
    while (
        attempts < 10
        and not ca_content.ok
        and b"The session has expired. You cannot keep the session unused for more than 60 mins."
        in ca_content.content
    ):
        attempts += 1
        click.echo(
            f"Unable to fetch PDF for CA bill {bill_id}, trying again after {attempts} seconds"
        )
        time.sleep(attempts)
        if metadata:
            url = metadata["url"]
        else:
            url = link
        url += f"?bill_id={bill_id}&version={bill_version}"
        new_request = requests.get(url)
        doc = lxml.html.fromstring(new_request.content)
        req_body["view_state"] = doc.get_element_by_id("j_id1:javax.faces.ViewState:0").value
        if metadata:
            ca_content = requests.post(metadata["url"], data=req_body, headers=req_headers)
        else:
            ca_content = requests.post(link, data=req_body, headers=req_headers)

    if not ca_content:
        click.echo(f"Could not fetch PDF for CA bill {bill_id}")
    elif not ca_content.ok:
        if ca_content.content:
            with open(
                f'temp_{bill_id}_{bill_version}_{time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())}.html',
                "wb",
            ) as f:
                click.echo(
                    f"Could not fetch PDF for CA bill {bill_id}; "
                    f"check {f.name} for the response ({ca_content.status_code})"
                )
                f.write(ca_content.content)
        else:
            click.echo(
                f"Could not fetch PDF for CA bill {bill_id} "
                f"{ca_content.status_code}: {ca_content.reason}"
            )
    if metadata:
        metadata["bill_id"] = bill_id
        metadata["bill_version"] = bill_version
        return ca_content, metadata
    return ca_content


def handle_california_pdf(data, metadata):
    """
    A few states have bills both with numbered lines and without.
    In these cases, we need to look at the start of the lines
    to determine which extraction function to use.

    In addition, CA requires an extra route call in order to get the actual PDF.
    This is done by getting a session token and making a new request.
    """

    # Data is the first CA HTML request content
    # metadata is the version
    # get and parse the initial CA page
    ca_content, metadata = get_pdf_from_link(metadata["url"], data=data, metadata=metadata)
    if not ca_content:
        if metadata and "bill_id" in metadata and "bill_version" in metadata:
            raise Exception(
                f'Could not fetch PDF for CA bill {metadata["bill_id"]} version {metadata["bill_version"]}'
            )
        raise Exception(f"Could not fetch PDF for CA bill")
    elif not ca_content.ok:
        if metadata and "bill_id" in metadata and "bill_version" in metadata:
            raise Exception(
                f'Could not fetch PDF for CA bill {metadata["bill_id"]} version {metadata["bill_version"]} '
                f"({ca_content.status_code}: {ca_content.reason})"
            )
        raise Exception(
            f"Could not fetch PDF for CA bill " f"({ca_content.status_code}: {ca_content.reason})"
        )

    return extract_sometimes_numbered_pdf(ca_content.content, metadata)
