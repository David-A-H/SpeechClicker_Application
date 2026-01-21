import sqlite3
import requests
import streamlit as st
from datetime import datetime

# --- CONFIG: Replace with your Zotero API key and library info ---
ZOTERO_API_KEY = "A3mf5yQmUGGCkyJIRUl2GdUS"
ZOTERO_USER_ID = "13989914"
ZOTERO_LIBRARY_TYPE = "user"  # "user" or "group"
ZOTERO_API_URL = f"https://api.zotero.org/{ZOTERO_LIBRARY_TYPE}s/{ZOTERO_USER_ID}/items"

# --- DATABASE SETUP ---
conn = sqlite3.connect("literature.db", check_same_thread=False)
c = conn.cursor()

# Literature table
c.execute('''
CREATE TABLE IF NOT EXISTS literature (
    id INTEGER PRIMARY KEY,
    zotero_key TEXT UNIQUE,
    authors TEXT,
    institutions TEXT,
    year INTEGER,
    title TEXT,
    journal TEXT,
    book_press TEXT,
    keyword_DV TEXT,
    keyword_IV TEXT,
    keyword_method_case TEXT,
    argument TEXT,
    method TEXT,
    evidence TEXT,
    implication TEXT,
    further_research TEXT,
    happy_thoughts TEXT,
    unhappy_thoughts TEXT,
    timestamp_created TEXT,
    timestamp_updated TEXT
)
''')

# Keywords table
c.execute('''
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT UNIQUE,
    type TEXT
)
''')

conn.commit()

# --- FUNCTIONS ---

def fetch_zotero_items_full():
    """Fetch Zotero items with full metadata"""
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    params = {"limit": 50}
    try:
        response = requests.get(ZOTERO_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            items = response.json()
            results = {}
            for item in items:
                data = item.get("data", {})
                title = data.get("title", "No Title")
                authors_list = data.get("creators", [])
                authors = ", ".join([a.get("lastName", "") for a in authors_list])
                journal = data.get("publicationTitle", "")
                year = data.get("date", "")
                book_press = data.get("publisher", "")
                zotero_key = data.get("key")
                display_name = f"{title} ({authors})"
                results[display_name] = {
                    "zotero_key": zotero_key,
                    "title": title,
                    "authors": authors,
                    "journal": journal,
                    "year": year,
                    "book_press": book_press
                }
            return results
        else:
            st.error(f"Failed to fetch Zotero items. Status code: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Error fetching Zotero items: {e}")
        return {}

def get_keywords(keyword_type):
    """Return a list of existing keywords for a given type"""
    c.execute("SELECT keyword FROM keywords WHERE type = ?", (keyword_type,))
    return [k[0] for k in c.fetchall()]

def add_keyword(keyword, keyword_type):
    """Add a new keyword to the pool if it doesn't exist"""
    if keyword.strip() == "":
        return
    try:
        c.execute("INSERT INTO keywords (keyword, type) VALUES (?, ?)", (keyword.strip(), keyword_type))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # already exists

def save_entry(zotero_key, fields):
    """Saves an entry to the database; prevents duplicates"""
    timestamp = datetime.now().isoformat()
    try:
        c.execute('''
            INSERT INTO literature (
                zotero_key, authors, institutions, year, title, journal, book_press,
                keyword_DV, keyword_IV, keyword_method_case,
                argument, method, evidence, implication, further_research,
                happy_thoughts, unhappy_thoughts, timestamp_created, timestamp_updated
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            zotero_key,
            fields['authors'],
            fields['institutions'],
            fields['year'],
            fields['title'],
            fields['journal'],
            fields['book_press'],
            fields['keyword_DV'],
            fields['keyword_IV'],
            fields['keyword_method_case'],
            fields['argument'],
            fields['method'],
            fields['evidence'],
            fields['implication'],
            fields['further_research'],
            fields['happy_thoughts'],
            fields['unhappy_thoughts'],
            timestamp,
            timestamp
        ))
        conn.commit()
        st.success("Entry saved successfully!")

        # Add new keywords to the pool
        add_keyword(fields['keyword_DV'], "DV")
        add_keyword(fields['keyword_IV'], "IV")
        add_keyword(fields['keyword_method_case'], "method_case")

    except sqlite3.IntegrityError:
        st.warning("This Zotero item is already in the database!")

# --- STREAMLIT GUI ---

st.title("📚 Literature Database with Zotero Integration")

# Step 1: Fetch Zotero items
zotero_items = fetch_zotero_items_full()
if not zotero_items:
    st.info("No Zotero items found. Check API key and User ID.")
else:
    selected = st.selectbox("Select a Zotero item", list(zotero_items.keys()))
    if selected:
        meta = zotero_items[selected]
        zotero_key = meta["zotero_key"]

        # --- Autofill bibliographic info ---
        st.subheader("Bibliographic Info")
        authors = st.text_input("Authors", value=meta["authors"])
        title = st.text_input("Title", value=meta["title"])
        journal = st.text_input("Journal", value=meta["journal"])
        year = st.number_input("Year", value=int(meta["year"].split("-")[0]) if meta["year"] else 2026)
        book_press = st.text_input("Book Press", value=meta["book_press"])
        institutions = st.text_input("Institutions (optional)")

        # --- Keywords ---
        st.subheader("Keywords")

        # DV keyword
        dv_options = ["<New Keyword>"] + get_keywords("DV")
        keyword_DV = st.selectbox("Keyword DV/Topic", dv_options)
        if keyword_DV == "<New Keyword>":
            keyword_DV = st.text_input("Enter new DV keyword")

        # IV keyword
        iv_options = ["<New Keyword>"] + get_keywords("IV")
        keyword_IV = st.selectbox("Keyword IV", iv_options)
        if keyword_IV == "<New Keyword>":
            keyword_IV = st.text_input("Enter new IV keyword")

        # Method/Case keyword
        method_options = ["<New Keyword>"] + get_keywords("method_case")
        keyword_method_case = st.selectbox("Keyword Method/Case", method_options)
        if keyword_method_case == "<New Keyword>":
            keyword_method_case = st.text_input("Enter new Method/Case keyword")

        # --- Analysis ---
        st.subheader("Analysis")
        argument = st.text_area("Argument")
        method = st.text_area("Method")
        evidence = st.text_area("Evidence")
        implication = st.text_area("Implication")
        further_research = st.text_area("Further Research")

        # --- Personal Thoughts ---
        st.subheader("Personal Thoughts")
        happy_thoughts = st.text_area("Susana's Happy Thoughts")
        unhappy_thoughts = st.text_area("Susana's Unhappy Thoughts")

        # --- Save Entry ---
        if st.button("Save Entry"):
            fields = {
                'authors': authors,
                'institutions': institutions,
                'year': year,
                'title': title,
                'journal': journal,
                'book_press': book_press,
                'keyword_DV': keyword_DV,
                'keyword_IV': keyword_IV,
                'keyword_method_case': keyword_method_case,
                'argument': argument,
                'method': method,
                'evidence': evidence,
                'implication': implication,
                'further_research': further_research,
                'happy_thoughts': happy_thoughts,
                'unhappy_thoughts': unhappy_thoughts
            }
            save_entry(zotero_key, fields)