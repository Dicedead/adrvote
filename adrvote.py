import argparse
import requests
import tqdm
import warnings
import re

import numpy as np
import pandas as pd

from typing import List, Callable, Dict
from bs4 import BeautifulSoup

ONLINE_VOTE = True

FOLDER_SECTIONLISTS = "res/sectionlists"
FOLDER_VOTERES = "votes/results"

EMAIL_COL = "Adresse e-mail"

DECISION_VOTE_MARKER = "DECISION"
PREFERENCES_VOTE_MARKER = "PREFERENCES"

SECTION_LIST = ["cms", "ar", "cgc", "gc", "gm", "el", "in", "sv", "ma", "mt", "ph", "mx", "sie", "sc", "if", "mte",
                "nx", "siq", "dh"]

SECTION_GROUPS = [["cms"], ["ar"], ["cgc"], ["gc"], ["gm"], ["el"], ["in"], ["sv", "nx"], ["ma"], ["mt"], ["ph", "siq"],
                  ["mx"], ["sie"], ["sc"], ["if", "mte", "dh"]]
SECTION_GROUPS = {"_".join(ls):ls for ls in SECTION_GROUPS}


def extract_names_from_html(html_content: str):
    soup = BeautifulSoup(html_content, 'html.parser')
    name_elements = soup.select('ul a')
    names = [element.get_text(strip=True) for element in name_elements]
    return names


def fetch_html_from(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        text_content = response.text
        return text_content

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")


def save_sectionlist(url: str, filename: str):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("\n".join(extract_names_from_html(fetch_html_from(url))))

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
        filename = f"{FOLDER_SECTIONLISTS}/{section}"
        save_sectionlist(url, filename)


def load_sections(reps: pd.DataFrame):
    reps_names = reps["Name"]
    reps_sections = [""] * len(reps_names)
    for i in tqdm.trange(len(reps_names)):
        for section in SECTION_LIST:
            if check_string_in_file(f"{FOLDER_SECTIONLISTS}/{section}", reps_names[i]):
                reps_sections[i] = section

    return reps_sections


def load_emails(reps: pd.DataFrame):
    reps_scipers = reps["Sciper"]
    reps_emails = [""] * len(reps_scipers)
    for i in tqdm.trange(len(reps_scipers)):
        sciper = reps_scipers[i]
        username = find_mail_username(fetch_html_from(f"https://people.epfl.ch/{sciper}"))
        reps_emails[i] = create_email_from_username(username)

    return reps_emails


def get_reps_df(reps_csv_path = "res/studentreps.csv", reload_sections: bool = False, reload_emails: bool = False):
    reps = pd.read_csv(reps_csv_path)
    if reload_sections:
        reps["Section"] = load_sections(reps)
    if reload_emails:
        reps["Email"] = load_emails(reps)
    return reps


def validate_emails(reps: pd.DataFrame, votesheet: pd.DataFrame):
    vote_emails = np.array(list(votesheet[EMAIL_COL]))
    reps_emails = np.array(list(reps["Email"] if ONLINE_VOTE else reps[reps["Présence"] == "TRUE"]["Email"]))
    valid_emails = [False] * len(vote_emails)

    for idx, email in enumerate(vote_emails):
        if email in reps_emails:
            valid_emails[idx] = True
        else:
            print(f"Invalid email {email}.")

    return valid_emails


def get_sections(reps: pd.DataFrame, emails: List[str]):
    sections = [""] * len(emails)

    for idx, email in enumerate(emails):
        for _, rep in reps.iterrows():
            if rep["Email"] == email:
                sections[idx] = rep["Section"]

    return sections


def aggreg_mean(scores: List[str]) -> str:
    int_scores = [int(s) for s in scores]
    return f"{np.mean(int_scores)}/10 (Sum: {np.sum(int_scores)} with {len(scores)})."


def aggreg_majority(votes: List[str]) -> str:
    num_yes = 0
    num_no = 0
    num_neutral = 0
    for vote in votes:
        if "Yes" in vote:
            num_yes += 1
        elif "No" in vote:
            num_no += 1
        else:
            num_neutral += 1
    total_res = "no vote"

    if num_yes >= num_no and num_yes > 0:
        total_res = "YES"
    elif num_no > num_yes and num_no > 0:
        total_res = "NO"

    return f"{total_res} (Yes: {num_yes} / No: {num_no} / Neutral: {num_neutral})."


def compute_single_vote_result(
        reps: pd.DataFrame,
        votesheet: pd.DataFrame,
        vote_col: str,
        aggreg: Callable[[List[str]], str]
):
    valid_emails = validate_emails(reps, votesheet)
    validated_sheet = votesheet[valid_emails]
    votes = validated_sheet[vote_col]
    overall_res = aggreg(votes)

    section_res = dict()
    sections = get_sections(reps, list(validated_sheet[EMAIL_COL]))
    for group in SECTION_GROUPS.keys():
        group_mask = [section in SECTION_GROUPS[group] for section in sections]
        section_votes = votes[group_mask]
        section_res[group] = aggreg(section_votes)

    return overall_res, section_res


def format_single_vote_result(title: str, overall_res: str, section_res: Dict[str, List[str]]):
    res = title + "\n"
    res += f"Total: {overall_res}\nPer section group:\n"
    for group in SECTION_GROUPS:
        res += f"{group}: {section_res[group]}\n"
    res += "\n"
    return res


def output_votes_results(
    reps: pd.DataFrame,
    votesheet: pd.DataFrame,
    output_file_path: str
):
    with warnings.catch_warnings(action="ignore"):
        res = output_file_path + "\n\n"
        for column in votesheet.columns:
            decision_col = DECISION_VOTE_MARKER in column
            preference_col = PREFERENCES_VOTE_MARKER in column
            if decision_col or preference_col:
                vote_res = compute_single_vote_result(reps, votesheet, column, aggreg_majority if decision_col else aggreg_mean)
                res += format_single_vote_result(column, *vote_res)

        with open(output_file_path, "w", encoding='utf-8') as file:
            file.write(res)

def run(
    input_csv_vote_path: str,
    output_file_path: str,
    reps_csv_path: str = None,
):
    if reps_csv_path is None:
        reps = get_reps_df()
    else:
        reps = get_reps_df(reps_csv_path, reload_sections=True, reload_emails=True)

    votesheet = pd.read_csv(input_csv_vote_path)
    output_votes_results(reps, votesheet, output_file_path)


def create_parser():
    parser = argparse.ArgumentParser("adrvote")

    parser.add_argument(
        "input_csv_vote_path",
        type=str,
        help="Path to input CSV file containing raw votes.",
    )

    parser.add_argument(
        "output_file_path",
        type=str,
        help="Path to file where to output vote results.",
    )

    parser.add_argument(
        "--reps_csv_path",
        type=str,
        default=None,
        help="Path to CSV file containing raw reps.",
    )

    return parser


def main():
    args = create_parser().parse_args()
    run(args.input_csv_vote_path, args.output_file_path, args.reps_csv_path)

if __name__ == "__main__":
    main()
