import streamlit as st
import google.generativeai as genai
import requests
import time

# Configure the API keys securely using Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# App Title and Description
st.title("AI-Powered Ghostwriter")
st.write("Generate high-quality content and check for originality using the power of Generative AI and Google Search.")

# Prompt Input Field
prompt = st.text_area("Enter your prompt:", placeholder="Write a blog about AI trends in 2025.")

# Initialize session tracking
if 'session_count' not in st.session_state:
    st.session_state.session_count = 0
if 'block_time' not in st.session_state:
    st.session_state.block_time = None

# Check if the user is blocked
if st.session_state.block_time:
    time_left = st.session_state.block_time - time.time()
    if time_left > 0:
        st.error(f"You have reached your session limit. Please try again in {int(time_left)} seconds.")
        st.write("Upgrade to Pro for unlimited content generation.")
        st.stop()
    else:
        st.session_state.block_time = None

# Limit sessions to 5
if st.session_state.session_count >= 5:
    st.session_state.block_time = time.time() + 15 * 60  # Block for 15 minutes
    st.error("You have reached the session limit. Please wait for 15 minutes or upgrade to Pro.")
    st.write("Upgrade to Pro for unlimited content generation.")
    st.stop()

# Generate Content Button
if st.button("Generate Response"):
    if not prompt.strip():
        st.error("Please enter a valid prompt.")
    else:
        try:
            # Generate content using Generative AI
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            generated_text = response.text.strip()

            # Increment session count
            st.session_state.session_count += 1

            # Display the generated content
            st.subheader("Generated Content:")
            st.write(generated_text)

            # Check if the content exists on the web
            st.subheader("Searching for Similar Content Online:")
            search_results = search_web(generated_text)

            if search_results:
                st.warning("Similar content found on the web:")

                # Create a dashboard-like display for the search results
                for result in search_results[:5]:  # Show top 5 results
                    with st.expander(result['title']):
                        st.write(f"**Source:** [{result['link']}]({result['link']})")
                        st.write(f"**Snippet:** {result['snippet']}")
                        st.write("---")

                # Option to regenerate content if similarity is found
                st.warning("To ensure 100% originality, you can regenerate the content.")
                if st.button("Regenerate Content"):
                    # Regenerate content by rewriting it for originality
                    regenerated_text = regenerate_content(generated_text)
                    st.session_state.generated_text = regenerated_text
                    st.success("Content has been regenerated for originality.")
                    st.subheader("Regenerated Content:")
                    st.write(regenerated_text)

            else:
                st.success("No similar content found online. Your content seems original!")

        except Exception as e:
            st.error(f"Error generating content: {e}")

# Display the regenerated content if applicable
if 'generated_text' in st.session_state:
    st.subheader("Regenerated Content (After Adjustments for Originality):")
    st.write(st.session_state.generated_text)

# Search Web Functionality
def search_web(query):
    """Searches the web using Google Custom Search API and returns results."""
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": st.secrets["GOOGLE_API_KEY"],
        "cx": st.secrets["GOOGLE_SEARCH_ENGINE_ID"],
        "q": query,
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        st.error(f"Search API Error: {response.status_code} - {response.text}")
        return []

# Function to regenerate and rewrite content to make it original
def regenerate_content(original_content):
    """Generates rewritten content based on the original content to ensure originality."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Explicitly request the model to rewrite and paraphrase the content.
    prompt = f"Rewrite the following content to make it original and distinct. Ensure it is paraphrased and does not match existing content:\n\n{original_content}"
    
    response = model.generate_content(prompt)
    return response.text.strip()
