import requests
import tqdm
import re

import pandas as pd

from bs4 import BeautifulSoup


SECTION_LIST = ["cms", "ar", "cgc", "gc", "gm", "el", "in", "sv", "ma", "mt", "ph", "mx", "sie", "sc", "if", "mte",
                "nx", "siq", "dh"]

SECTION_GROUPS = [["cms"], ["ar"], ["cgc"], ["gc"], ["gm"], ["el"], ["in"], ["sv", "nx"], ["ma"], ["mt"], ["ph", "siq"],
                  ["mx"], ["sie"], ["sc"], ["if", "mte", "dh"]]


def extract_names_from_html(html_content: str):
    soup = BeautifulSoup(html_content, 'html.parser')
    name_elements = soup.select('ul a')
    names = [element.get_text(strip=True) for element in name_elements]
    return names


def fetch_text_from(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        text_content = response.text
        return text_content

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")


def save_sectionlist(url: str, filename: str):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("\n".join(extract_names_from_html(fetch_text_from(url))))

    print(f"Content from {url} has been saved to {filename}.")



def check_string_in_file(file_path, search_string):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return search_string in content
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return False


def find_mail_username(html_content: str):
    pattern = r"documentURI\.replace\(re,\s*'([^']+)'\)"
    match = re.search(pattern, html_content)

    if match:
        return match.group(1)

    pattern = r"var re = /([^/]+)/"
    raise ValueError(f"Could not find mail username for {re.search(pattern, html_content).group(1)}")


def create_email_from_username(username: str):
    return f"{username}@epfl.ch"


def update_sections():
    for section in SECTION_LIST:
        url = f"https://cadiwww.epfl.ch/listes/viewlist?list=etudiants.{section}@epfl.ch"
        filename = f"res/sectionlists/{section}"
        save_sectionlist(url, filename)


def load_sections(reps: pd.DataFrame):
    reps_names = reps["Name"]
    reps_sections = [""] * len(reps_names)
    for i in tqdm.trange(len(reps_names)):
        for section in SECTION_LIST:
            if check_string_in_file(f"res/sectionlists/{section}", reps_names[i]):
                reps_sections[i] = section

    return reps_sections


def load_emails(reps: pd.DataFrame):
    reps_scipers = reps["Sciper"]
    reps_emails = [""] * len(reps_scipers)
    for i in tqdm.trange(len(reps_scipers)):
        sciper = reps_scipers[i]
        username = find_mail_username(fetch_text_from(f"https://people.epfl.ch/{sciper}"))
        reps_emails[i] = create_email_from_username(username)

    return reps_emails


def get_reps_df(reps_csv_path = "res/studentreps.csv", get_sections: bool = False, get_emails: bool = False):
    reps = pd.read_csv(reps_csv_path)
    if get_sections:
        reps["Section"] = load_sections(reps)
    if get_emails:
        reps["Email"] = load_emails(reps)
    return reps


if __name__ == "__main__":
    update_sections()
    reps = get_reps_df()
    emails = reps["Section"]
    for e in emails:
        print(e)
