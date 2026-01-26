import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --------------------------
# Database functions
# --------------------------

def save_label(db_path, entry_id, entry_text, variable_labels, table_name="annotations"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check table
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not c.fetchone():
        cols_sql = ", ".join([f"{var} TEXT" for var in variable_labels.keys()])
        c.execute(
            f"""
            CREATE TABLE {table_name} (
                id TEXT PRIMARY KEY,
                text TEXT,
                timestamp TEXT,
                {cols_sql}
            )
            """
        )
    else:
        c.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [info[1] for info in c.fetchall()]
        for col in ["timestamp"] + list(variable_labels.keys()):
            if col not in existing_cols:
                c.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} TEXT")

    timestamp = datetime.utcnow().isoformat()

    columns = ["id", "text", "timestamp"] + list(variable_labels.keys())
    placeholders = ", ".join("?" for _ in columns)
    values = [entry_id, entry_text, timestamp] + list(variable_labels.values())

    c.execute(
        f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
        values
    )

    conn.commit()
    conn.close()


def get_all_entries(db_path, table_name="annotations"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not c.fetchone():
        conn.close()
        return pd.DataFrame()
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


# --------------------------
# Streamlit App
# --------------------------

st.title("📄 Conditional Multi-variable Annotation Tool")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

st.sidebar.header("Database")

# Initialize session state
if "db_path" not in st.session_state:
    st.session_state.db_path = None

# Option 1: Upload existing DB
uploaded_db = st.sidebar.file_uploader(
    "Use existing SQLite database",
    type=["db"],
    key="db_uploader"
)

if uploaded_db:
    db_path = f"/tmp/{uploaded_db.name}"
    with open(db_path, "wb") as f:
        f.write(uploaded_db.getbuffer())
    st.session_state.db_path = db_path
    st.sidebar.success(f"Using existing DB: {uploaded_db.name}")

# Option 2: Create new DB
new_db_name = st.sidebar.text_input(
    "Or create new database",
    value="annotations.db"
)

if st.sidebar.button("Create / Use New DB"):
    st.session_state.db_path = new_db_name
    st.sidebar.success(f"Using database: {new_db_name}")

# Block app until DB is selected
if not st.session_state.db_path:
    st.warning("Please select or create a database to continue.")
    st.stop()


if uploaded_file:
    df_csv = pd.read_csv(uploaded_file)
    st.success("CSV loaded successfully")
    st.write("Detected columns:", df_csv.columns.tolist())

    id_column = st.selectbox("Select ID column", df_csv.columns.tolist())
    text_column = st.selectbox("Select text column to annotate", df_csv.columns.tolist())

    if df_csv[id_column].isna().any():
        st.error("❌ ID column contains missing values.")
        st.stop()

    # --------------------------
    # Variable definition
    # --------------------------

    st.subheader("Define Variables & Labels (use 'if' for conditionals)")
    var_input = st.text_area(
        "Examples:\n"
        "parent1:yes,no\n"
        "child1:TEXT if parent1=yes\n"
        "child2:0,1 if parent1=no",
        value="parent1:yes,no\nchild1:TEXT if parent1=yes\nchild2:0,1 if parent1=no"
    )

    variables = []
    for line in var_input.strip().splitlines():
        if ":" not in line:
            continue

        var_part, labels_part = line.split(":", 1)
        var_name = var_part.strip()
        labels_part = labels_part.strip()

        if "if" in labels_part:
            labels, condition = labels_part.split("if", 1)
            var_type = "TEXT" if labels.strip().upper() == "TEXT" else [l.strip() for l in labels.split(",")]
            variables.append({
                "name": var_name,
                "type": var_type,
                "condition": condition.strip()
            })
        else:
            var_type = "TEXT" if labels_part.upper() == "TEXT" else [l.strip() for l in labels_part.split(",")]
            variables.append({
                "name": var_name,
                "type": var_type,
                "condition": None
            })

    if not variables:
        st.error("❌ Please define at least one variable.")
        st.stop()

    # --------------------------
    # Filter already-annotated entries
    # --------------------------

    df_db = get_all_entries(st.session_state.db_path)
    annotated_ids = set(df_db["id"].astype(str)) if not df_db.empty else set()

    df_new = df_csv.copy()
    if "shuffled_ids" not in st.session_state:
        df_new = df_new.sample(frac=1, random_state=None).reset_index(drop=True)
        st.session_state.shuffled_ids = df_new["id"].tolist()
    else:
        df_new = df_new.set_index("id").loc[st.session_state.shuffled_ids].reset_index()
    df_new["id"] = df_new[id_column].astype(str)
    df_new = df_new[~df_new["id"].isin(annotated_ids)]
    

    if df_new.empty:
        st.success("🎉 All entries have already been annotated!")
        st.stop()

    st.info(f"🆕 {len(df_new)} entries remaining to annotate")

    # --------------------------
    # Navigation
    # --------------------------

    st.sidebar.header("Navigation")
    entry_ids = df_new["id"].tolist()

    current_index = st.sidebar.number_input(
        "Entry index",
        min_value=0,
        max_value=len(entry_ids) - 1,
        value=0
    )

    current_entry = df_new.iloc[current_index]

    st.subheader(
        f"Entry {current_index + 1} / {len(entry_ids)} (ID: {current_entry['id']})"
    )

    st.text_area(
        "Text to annotate",
        current_entry[text_column],
        height=400
    )

    # --------------------------
    # Annotation UI
    # --------------------------

    selected_labels = {}
    parent_values = {}

    for var in variables:
        var_name = var["name"]
        var_type = var["type"]
        condition = var["condition"]

        if condition:
            cond_var, cond_value = condition.split("=")
            cond_var = cond_var.strip()
            cond_value = cond_value.strip()

            if parent_values.get(cond_var) != cond_value:
                continue

        if var_type == "TEXT":
            selected_labels[var_name] = st.text_area(
                f"{var_name} (free text)",
                height=100
            )
        else:
            options = ["— select —"] + var_type
            choice = st.radio(var_name, options, index=0, key=f"{var_name}_{current_entry['id']}")

            if choice != "— select —":
                selected_labels[var_name] = choice
                parent_values[var_name] = choice
            else:
                selected_labels[var_name] = None

    # --------------------------
    # Save & Export
    # --------------------------

    if st.button("💾 Save Labels"):
        save_label(
            st.session_state.db_path,
            current_entry["id"],
            current_entry[text_column],
            selected_labels)
        st.success(f"Saved annotation for ID {current_entry['id']}")

    if st.button("📤 Export All Annotations to CSV"):
        df_export = get_all_entries(st.session_state.db_path)
        export_path = "annotated_export.csv"
        df_export.to_csv(export_path, index=False, encoding="utf-8")
        st.success(f"Exported annotations to {export_path}")
