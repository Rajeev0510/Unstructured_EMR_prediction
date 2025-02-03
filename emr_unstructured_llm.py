import streamlit as st
import pandas as pd
import re
import spacy
import subprocess
import sys
from docx import Document
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Ensure the SpaCy model is installed
import spacy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")  # Use a blank English model as a fallback

# Function to extract structured data from the DOCX file
def extract_emr_data(doc_file):
    doc = Document(doc_file)
    text = [p.text for p in doc.paragraphs if p.text.strip()]
    
    patients = []
    patient_data = {}
    
    for line in text:
        if line.startswith("Patient "):  # New patient section
            if patient_data:
                patients.append(patient_data)
            patient_data = {}
        else:
            key_val = line.split(": ", 1)
            if len(key_val) == 2:
                key, val = key_val
                patient_data[key.strip()] = val.strip()
    
    if patient_data:
        patients.append(patient_data)
    
    return pd.DataFrame(patients)

# Function to extract structured data from manual input text
def extract_text_input(input_text):
    patients_data = []
    for entry in input_text.split("\n\n"):  # Assume each entry is separated by a blank line
        lines = entry.split(". ")
        patient_info = {}
        try:
            for line in lines:
                if "year-old" in line:
                    age_str = line.split("-year-old")[0].strip()
                    if age_str.isdigit():
                        patient_info["Age"] = int(age_str)
                if "weeks gestation" in line:
                    gest_age_str = line.split(" weeks gestation")[0].split()[-1]
                    if gest_age_str.isdigit():
                        patient_info["Gestational Age"] = int(gest_age_str)
                if "hemoglobin" in line:
                    try:
                        patient_info["Hemoglobin"] = float(line.split("hemoglobin at ")[1].split(" g/dL")[0])
                    except:
                        patient_info["Hemoglobin"] = None
                if "blood pressure" in line:
                    patient_info["Blood Pressure"] = line.split("blood pressure (")[1].split(")")[0]
                if "medications include" in line:
                    patient_info["Medications"] = line.split("medications include ")[1].split(".")[0]
            if patient_info:
                patients_data.append(patient_info)
        except Exception as e:
            st.warning(f"Error processing entry: {entry} | Error: {e}")
    
    return pd.DataFrame(patients_data) if patients_data else pd.DataFrame()

# Function to categorize risk level
def categorize_risk(row):
    if row.get("Hemoglobin") and row["Hemoglobin"] < 11:
        return "High"
    if row.get("Gestational Age") and row["Gestational Age"] < 37:
        return "Preterm Risk"
    return "Low"

# Function to generate health suggestions
def generate_suggestions(row):
    suggestions = []
    
    if row["Risk Level"] == "High":
        suggestions.append("Monitor fetal health closely and consult a specialist.")
    if row["Risk Level"] == "Preterm Risk":
        suggestions.append("Schedule regular prenatal visits to monitor progression.")
    if row["Risk Level"] == "Low":
        suggestions.append("Maintain a healthy diet and follow standard prenatal care.")
    
    if row.get("Hemoglobin") and row["Hemoglobin"] < 11:
        suggestions.append("Consider iron supplements and iron-rich foods.")
    
    if row.get("Gestational Age") and row["Gestational Age"] < 37:
        suggestions.append("Ensure adequate hydration and rest.")
    
    return " | ".join(suggestions)

# Streamlit App
st.title("EMR Data Analysis & Prediction")

# Manual Data Input
st.subheader("Enter EMR Notes")
input_text = st.text_area("Input EMR notes here:")

if input_text:
    structured_data = extract_text_input(input_text)
    if not structured_data.empty:
        structured_data["Risk Level"] = structured_data.apply(categorize_risk, axis=1)
        structured_data["Health Suggestions"] = structured_data.apply(generate_suggestions, axis=1)

        st.subheader("Structured Data with Predictions (Text Input)")
        st.dataframe(structured_data)

        # Download processed data
        csv = structured_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Results as CSV (Text Input)",
            data=csv,
            file_name="emr_predictions_text_input.csv",
            mime="text/csv",
        )
    else:
        st.warning("No valid patient data extracted from input. Please check formatting.")

# File upload option
st.subheader("Upload EMR Data")
uploaded_file = st.file_uploader("Upload a .docx file", type=["docx"])

if uploaded_file is not None:
    emr_df = extract_emr_data(uploaded_file)
    
    if emr_df.empty:
        st.warning("No valid patient data extracted from the document.")
    else:
        emr_df["Risk Level"] = emr_df.apply(categorize_risk, axis=1)
        emr_df["Health Suggestions"] = emr_df.apply(generate_suggestions, axis=1)

        st.subheader("Structured Data with Predictions (.docx Upload)")
        st.dataframe(emr_df)

        # Download processed data
        csv = emr_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Results as CSV (.docx Upload)",
            data=csv,
            file_name="emr_predictions_docx_upload.csv",
            mime="text/csv",
        )
