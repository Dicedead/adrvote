import requests
from bs4 import BeautifulSoup


SECTION_LIST = ["cgc"]


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

if __name__ == "__main__":
    url = "https://cadiwww.epfl.ch/listes/viewlist?list=etudiants.dh@epfl.ch"
    filename = "res/sectionlists/dh"
    fetch_and_save_text(url, filename)
