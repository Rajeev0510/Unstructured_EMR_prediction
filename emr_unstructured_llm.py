import pandas as pd
import streamlit as st
import spacy
from docx import Document

# Ensure that the 'spacy' library is installed and the 'en_core_web_sm' model is downloaded.
# Run 'pip install spacy' and 'python -m spacy download en_core_web_sm' if not already installed.
nlp = spacy.load("en_core_web_sm")

# Function to read text from a Word document
def read_word_file(uploaded_file):
    doc = Document(uploaded_file)
    patients_data = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            # Assume each paragraph corresponds to one patient's data
            patients_data.append(text)
    return patients_data

# Add predictions and recommendations
def add_predictions(data):
    predictions = []
    recommendations = []
    for _, row in data.iterrows():
        fetal_health = "Normal" if row.get("Hemoglobin", "normal") == "normal" else "At Risk"
        gestational_term = "Full Term" if row.get("Gestational Age") and int(row["Gestational Age"] or 0) >= 37 else "Preterm"

        # Generate recommendations based on predictions
        recommendation = []
        if fetal_health == "At Risk":
            recommendation.append("Monitor fetal health closely and consult a specialist.")
        if gestational_term == "Preterm":
            recommendation.append("Schedule regular prenatal visits to monitor progression.")
        if fetal_health == "Normal" and gestational_term == "Full Term":
            recommendation.append("Maintain a healthy diet and follow standard prenatal care.")
        
        predictions.append({
            "Fetal Health": fetal_health, 
            "Gestational Term": gestational_term
        })
        recommendations.append(" ".join(recommendation))
    
    predictions_df = pd.DataFrame(predictions)
    recommendations_df = pd.DataFrame({"Recommendations": recommendations})
    return pd.concat([data, predictions_df, recommendations_df], axis=1)

# Streamlit app
def main():
    st.title("Predict Patient's EMR Data")

    # Text input option
    st.subheader("Enter EMR Notes")
    input_text = st.text_area("Input EMR notes here:")

    # File upload options
    st.subheader("Upload EMR Data")
    uploaded_file = st.file_uploader("Upload a .docx file", type=["docx"])

    if input_text:
        # Process text input
        structured_data = pd.DataFrame([{  # Example structured format
            "Age": 30,
            "Gestational Age": 32,
            "Hemoglobin": "normal"
        }])
        results = add_predictions(structured_data)

        # Display results for text input
        st.subheader("Structured Data with Predictions (Text Input)")
        st.dataframe(results)

        # Download results for text input
        csv = results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Results as CSV (Text Input)",
            data=csv,
            file_name="emr_predictions_text_input.csv",
            mime="text/csv",
        )

    elif uploaded_file is not None:
        if uploaded_file.name.endswith(".docx"):
            patient_notes = read_word_file(uploaded_file)

            # Process multiple patients' data
            structured_data = pd.DataFrame([{  # Example structured format for each patient
                "Age": 30 + i,  # Example variation for each patient
                "Gestational Age": 32 - i,  # Example variation
                "Hemoglobin": "normal" if i % 2 == 0 else "low"
            } for i, _ in enumerate(patient_notes)])

            results = add_predictions(structured_data)

            # Display results for .docx upload
            st.subheader("Structured Data with Predictions (.docx Upload)")
            st.dataframe(results)

            # Download results for .docx upload
            csv = results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV (.docx Upload)",
                data=csv,
                file_name="emr_predictions_docx_upload.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    main()
