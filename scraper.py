import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import unicodedata

base_url = "https://capitol.texas.gov"
urls = {
    "House": f"{base_url}/Committees/MeetingsUpcoming.aspx?Chamber=H",
    "Senate": f"{base_url}/Committees/MeetingsUpcoming.aspx?Chamber=S",
}

# Function to clean text
def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')

# Function to extract weekday
def extract_weekday(date_text):
    try:
        match = re.search(r"([A-Za-z]+ \d{1,2}, \d{4})", date_text)
        if match:
            return datetime.strptime(match.group(1), "%B %d, %Y").strftime("%A")
    except ValueError:
        pass
    return "Unknown"

# Scrape data
data = []
for chamber, url in urls.items():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    meeting_links = [base_url + a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith(".HTM")]

    for link in meeting_links:
        meeting_response = requests.get(link)
        meeting_soup = BeautifulSoup(meeting_response.text, "html.parser")

        committee_name = next((p.text.split(":")[-1].strip() for p in meeting_soup.find_all("p") if "COMMITTEE:" in p.text), "Unknown Committee")
        meeting_day = next((extract_weekday(p.text) for p in meeting_soup.find_all("p") if "TIME & DATE:" in p.text), "Unknown")

        for td in meeting_soup.find_all("td"):
            bill_link = td.find("a")
            if bill_link and "Bill=" in bill_link["href"]:
                bill_number = bill_link.text.strip()
                full_text = td.get_text("\n").strip()
                text_parts = list(filter(None, full_text.split("\n")))

                bill_author = normalize_text(text_parts[1]) if len(text_parts) > 1 else "Unknown"
                caption = " ".join(text_parts[2:]).strip() if len(text_parts) > 2 else "No Caption"

                data.append([chamber, meeting_day, committee_name, bill_number, bill_author, caption])

df = pd.DataFrame(data, columns=["Chamber", "Day", "Committee Name", "Bill Number", "Bill Author", "Caption"])
df["Stance"] = ""
del df[df.columns[0]]
df.to_csv("bills.csv", index=False)


