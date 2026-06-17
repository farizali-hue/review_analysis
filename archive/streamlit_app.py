import os
import io
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from neg_issue import generate_negative_issue

# Load .env
load_dotenv()

st.set_page_config(page_title="Negative Issue Tagger", layout="wide")

st.title("Negative Issue Tagger")
st.write("Upload a reviews file (Excel or CSV). The app filters ratings < 4 and generates a single-word negative issue per review.")

uploaded = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "xls", "csv"]) 

if uploaded is not None:
    # read file into dataframe
    try:
        if uploaded.name.endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

    st.write(f"Loaded {len(df)} rows")

    if 'Rating' not in df.columns:
        st.error("Input file must contain a 'Rating' column.")
        st.stop()

    # Filter low ratings
    low_df = df[df['Rating'] < 4].reset_index(drop=True)
    low_df = low_df[~low_df['Content'].isna()] if 'Content' in low_df.columns else low_df

    st.write(f"Found {len(low_df)} low-rating rows")
    st.dataframe(low_df.head(10))

    if st.button("Generate Negative Issues"):
        if len(low_df) == 0:
            st.info("No rows to process.")
        else:
            results = []
            progress = st.progress(0)
            status_text = st.empty()
            error_container = st.container()
            
            try:
                for i, row in low_df.iterrows():
                    title = row.get('Title', '') if 'Title' in row else ''
                    content = row.get('Content', '') if 'Content' in row else ''
                    status_text.text(f"Processing row {i+1}/{len(low_df)}... Title: {title[:50]}")
                    
                    issue = generate_negative_issue(title, content)
                    results.append(issue)
                    progress.progress(int((i + 1) / len(low_df) * 100))

                low_df['Negative Issue'] = results
                status_text.empty()
                st.success(f'Done! Generated issues for {len(low_df)} rows')
                st.dataframe(low_df[['Title','Content','Negative Issue']].head(20))

                # allow download
                csv = low_df.to_csv(index=False).encode('utf-8')
                st.download_button('Download results CSV', data=csv, file_name='negative_issues.csv', mime='text/csv')
            except Exception as e:
                import traceback
                error_container.error(f"Error: {str(e)}")
                error_container.code(traceback.format_exc(), language="python")

else:
    st.info('Upload a file to begin')
