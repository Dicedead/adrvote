import requests
import tqdm

import pandas as pd

from bs4 import BeautifulSoup


SECTION_LIST = ["cms", "ar", "cgc", "gc", "gm", "el", "in", "sv", "ma", "mt", "ph", "mx", "sie", "sc", "if", "mte",
                "nx", "siq", "dh"]


def extract_names_from_html(html_content: str):
    soup = BeautifulSoup(html_content, 'html.parser')
    name_elements = soup.select('ul a')
    names = [element.get_text(strip=True) for element in name_elements]
    return names


def fetch_and_save_text(url: str, filename: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        text_content = response.text

        with open(filename, 'w', encoding='utf-8') as file:
            file.write("\n".join(extract_names_from_html(text_content)))

        print(f"Content from {url} has been saved to {filename}.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")


def check_string_in_file(file_path, search_string):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return search_string in content
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return False


def update_sections():

    for section in SECTION_LIST:
        url = f"https://cadiwww.epfl.ch/listes/viewlist?list=etudiants.{section}@epfl.ch"
        filename = f"res/sectionlists/{section}"
        fetch_and_save_text(url, filename)

    reps_csv_path = "res/studentreps.csv"
    reps = pd.read_csv(reps_csv_path)

    reps_names = reps["Name"]
    reps_sections = [""] * len(reps_names)
    for i in tqdm.trange(len(reps_names)):
        for section in SECTION_LIST:
            if check_string_in_file(f"res/sectionlists/{section}", reps_names[i]):
                reps_sections[i] = section
    reps["Section"] = reps_sections

    return reps, reps_sections


if __name__ == "__main__":
    res, res2 = update_sections()
    print(res)
