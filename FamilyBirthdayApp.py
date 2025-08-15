import streamlit as st
import pandas as pd
import datetime
import openai
import pywhatkit
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load OpenAI key from secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["GOOGLE_SHEETS_KEY"], scope)
client = gspread.authorize(creds)
sheet = client.open("FamilyBirthdays").sheet1

# Read existing data
data = sheet.get_all_records()
df = pd.DataFrame(data)

# UI
st.title("🎉 Family Birthday Manager (Google Sheets Edition)")
menu = ["Add Birthday", "View Birthdays", "Send Today's Wishes"]
choice = st.sidebar.selectbox("Menu", menu)

# Add Birthday
if choice == "Add Birthday":
    st.subheader("➕ Add a Family Member")
    name = st.text_input("Full Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    relation = st.text_input("Relation (e.g., Brother, Mother)")
    birthday = st.date_input("Birthday")
    phone = st.text_input("WhatsApp Number (with country code)")

    if st.button("Save"):
        sheet.append_row([name, gender, relation, birthday.strftime("%Y-%m-%d"), phone])
        st.success(f"Saved birthday for {name} 🎂")

# View Birthdays
elif choice == "View Birthdays":
    st.subheader("📅 All Birthdays")
    st.dataframe(df.sort_values("Birthday"))

# Send Today's Wishes
elif choice == "Send Today's Wishes":
    today = datetime.date.today().strftime("%m-%d")
    today_birthdays = df[df["Birthday"].str[5:] == today]

    if not today_birthdays.empty:
        for _, row in today_birthdays.iterrows():
            prompt = f"Write a short, funny birthday wish for my {row['Relation']} named {row['Name']} ({row['Gender']})."
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            wish = response.choices[0].message["content"].strip()

            st.write(f"To {row['Name']}: {wish}")
            pywhatkit.sendwhatmsg_instantly(row["Phone"], wish)
            st.success(f"WhatsApp message sent to {row['Name']}")
    else:
        st.info("No birthdays today 🎂")
