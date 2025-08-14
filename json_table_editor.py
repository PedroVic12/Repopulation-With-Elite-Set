import streamlit as st
import json

# Define the JSON file path
JSON_FILE = 'data.json'

# Load data from JSON file (or create an empty structure if file doesn't exist)
try:
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"name": "", "age": "", "city": "", "cross": "", "mutation": ""} # Example empty structure

st.title("Edit JSON Data")

# Create textboxes and pre-fill with existing data
name = st.text_input("Name", value=data.get("name", ""))
age = st.text_input("Age", value=data.get("age", ""))
city = st.text_input("City", value=data.get("city", ""))
cross = st.text_input("cross", value=data.get("cross", ""))
mutation = st.text_input("mutation", value=data.get("mutation", ""))

if st.button("Save Changes"):
    data["name"] = name
    data["age"] = age
    data["city"] = city
    data["cross"] = cross
    data["mutation"] = mutation

    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=4) # indent for pretty printing
    st.success("Data saved successfully!")
    st.json(data)  # Display the current JSON data

if st.button("Read JSON"):
    # Load data from JSON file (or create an empty structure if file doesn't exist)
    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
        st.success("Data read successfully!")
    except FileNotFoundError:
        data = {"name": "", "age": "", "city": "", "cross": "", "mutation": ""}  # Example empty structure
    st.json(data)  # Display the current JSON data