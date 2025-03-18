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
        committee_name = re.sub(r"\s+", " ", committee_name).strip()  # Clean extra spaces

        meeting_day = next((extract_weekday(p.text) for p in meeting_soup.find_all("p") if "TIME & DATE:" in p.text), "Unknown")

        for td in meeting_soup.find_all("td"):
            bill_link = td.find("a")
            if bill_link and "Bill=" in bill_link["href"]:
                bill_number = bill_link.text.strip()
                full_text = td.get_text("\n").strip()
                text_parts = list(filter(None, full_text.split("\n")))

                bill_author = text_parts[1].strip() if len(text_parts) > 1 else "Unknown"
                if len(text_parts) > 2 and not text_parts[2].startswith("Relating to"):
                    bill_author += " " + text_parts[2].strip()
                bill_author = re.sub(r"\s+", " ", bill_author).strip()

                caption_start = 2 if bill_author != "Unknown" else 1
                caption = " ".join(text_parts[caption_start:]).strip()

                bill_author_cleaned = re.escape(bill_author.replace(",", "").strip())
                caption = re.sub(rf"^\s*{bill_author_cleaned}\s*", "", caption).strip()

                first_name = bill_author.split()[0]
                caption = re.sub(rf"^\s*{re.escape(first_name)}\s*", "", caption).strip()

                caption = re.sub(r"\s+", " ", caption)
                caption = caption.replace("\xa0", " ").strip()

                caption = caption.replace("Relating to Relating to", "Relating to").strip()

                data.append([chamber, meeting_day, committee_name, bill_number, bill_author, caption])


df = pd.DataFrame(data, columns=["Chamber", "Day", "Committee Name", "Bill Number", "Bill Author", "Caption"])
df["Stance"] = ""
df["Action"] = ""

for i in range(len(df)):
    n = df['Bill Author'][i]
    if " " in n:
        name = n.split()[1:]
        for x in name:
            if x in df['Caption'][i]:
                df['Caption'][i] = df['Caption'][i].replace(x, " ").strip()
                
df.to_csv("bills.csv", index=False)
