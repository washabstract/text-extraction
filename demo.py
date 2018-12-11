import csv
import os
import sys
import scrapelib
import click
from extract import extract_text


MIMETYPES = {
    'application/pdf': 'pdf',
    'text/html': 'html',
    'application/msword': 'doc',
    'application/rtf': 'rtf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
}

scraper = scrapelib.Scraper()


def jid_to_abbr(j):
    return j.split(':')[-1].split('/')[0]


def download(version):
    abbr = jid_to_abbr(version['jurisdiction_id'])
    ext = MIMETYPES[version["media_type"]]
    filename = f'raw/{abbr}/{version["session"]}-{version["identifier"]}.{ext}'

    if not os.path.exists(filename):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError:
            pass
        _, resp = scraper.urlretrieve(version['url'], filename)
        return filename, resp
    else:
        with open(filename, 'rb') as f:
            return filename, f.read()


def extract_to_file(filename, data, version):
    text = extract_text(filename, data, version)

    text_filename = filename.replace('raw/', 'text/') + '.txt'
    try:
        os.makedirs(os.path.dirname(text_filename))
    except OSError:
        pass
    with open(text_filename, 'w') as f:
        f.write(text)

    return text_filename, len(text)


def main():
    state = sys.argv[1]
    with open('sample.csv') as f:
        for version in csv.DictReader(f):
            if jid_to_abbr(version['jurisdiction_id']) == state:
                filename, data = download(version)
                text_filename, bytes = extract_to_file(filename, data, version)
                print(f'{filename} => {text_filename} ({bytes} bytes)')


if __name__ == '__main__':
    main()
