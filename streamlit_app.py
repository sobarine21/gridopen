import streamlit as st
import google.generativeai as genai
import requests
import time
from requests_oauthlib import OAuth2Session

# ---- OAuth Configuration ----
client_id = st.secrets["oauth"]["client_id"]
client_secret = st.secrets["oauth"]["client_secret"]
redirect_uri = "https://gridopen.streamlit.app/"  # Your app's URL (main URL)
auth_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://oauth2.googleapis.com/token"
api_base_url = "https://www.googleapis.com/plus/v1/people/me"  # To get user information

# ---- Helper Functions ----

def initialize_session():
    """Initializes session state variables."""
    if 'session_count' not in st.session_state:
        st.session_state.session_count = 0
    if 'block_time' not in st.session_state:
        st.session_state.block_time = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None  # Store user info after authentication

def check_session_limit():
    """Checks if the user has reached the session limit and manages block time."""
    if st.session_state.block_time:
        time_left = st.session_state.block_time - time.time()
        if time_left > 0:
            st.error(f"You have reached your session limit. Please try again in {int(time_left)} seconds.")
            st.write("Upgrade to Pro for unlimited content generation.")
            st.stop()
        else:
            st.session_state.block_time = None

    if st.session_state.session_count >= 5:
        st.session_state.block_time = time.time() + 15 * 60  # Block for 15 minutes
        st.error("You have reached the session limit. Please wait for 15 minutes or upgrade to Pro.")
        st.write("Upgrade to Pro for unlimited content generation.")
        st.stop()

def generate_content(prompt):
    """Generates content using Generative AI."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating content: {e}")
        raise

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

def display_search_results(search_results):
    """Displays search results in a structured format."""
    if search_results:
        st.warning("Similar content found on the web:")

        for result in search_results[:5]:  # Show top 5 results
            with st.expander(result['title']):
                st.write(f"**Source:** [{result['link']}]({result['link']})")
                st.write(f"**Snippet:** {result['snippet']}")
                st.write("---")

        st.warning("To ensure 100% originality, you can regenerate the content.")
        if st.button("Regenerate Content"):
            regenerate_and_display_content()
    else:
        st.success("No similar content found online. Your content seems original!")

def regenerate_and_display_content():
    """Regenerates content and displays it after ensuring originality."""
    original_text = st.session_state.generated_text
    regenerated_text = regenerate_content(original_text)
    st.session_state.generated_text = regenerated_text
    st.success("Content has been regenerated for originality.")
    st.subheader("Regenerated Content:")
    st.write(regenerated_text)

def regenerate_content(original_content):
    """Generates rewritten content based on the original content to ensure originality."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Rewrite the following content to make it original and distinct. Ensure it is paraphrased and does not match existing content:\n\n{original_content}"
    response = model.generate_content(prompt)
    return response.text.strip()

# ---- OAuth Flow Functions ----

def handle_redirect():
    """Handles the OAuth redirect after the user logs in."""
    query_params = st.experimental_get_query_params()
    if 'code' in query_params:
        code = query_params['code'][0]

        # OAuth2 session setup
        oauth_session = OAuth2Session(client_id, redirect_uri=redirect_uri)
        
        # Exchange the code for an access token
        token = oauth_session.fetch_token(token_url, client_secret=client_secret, code=code)

        # Fetch user info
        user_info_response = oauth_session.get(api_base_url)
        user_info = user_info_response.json()

        # Store user info in session state
        st.session_state.user_info = user_info
        st.write(f"Welcome {user_info.get('displayName')}")
        
        # Redirect (rerun) to avoid showing the `code` in the URL
        st.experimental_rerun()

def login_oauth():
    """Handles OAuth login."""
    # OAuth2 session setup
    oauth_session = OAuth2Session(client_id, redirect_uri=redirect_uri)
    
    # Generate the authorization URL
    authorization_url, state = oauth_session.authorization_url(auth_base_url, access_type="offline", prompt="select_account")
    
    st.write(f"Please log in with Google: [Login]({authorization_url})")

# ---- Main Streamlit App ----

# Check if user is logged in, show login if not
if 'user_info' not in st.session_state:
    if 'code' in st.experimental_get_query_params():
        handle_redirect()
    else:
        login_oauth()
else:
    # App Title and Description
    st.title("AI-Powered Ghostwriter")
    st.write(f"Welcome, {st.session_state['user_info']['displayName']}!")
    st.write("Generate high-quality content and check for originality using the power of Generative AI and Google Search.")

    # Initialize session tracking
    initialize_session()

    # Prompt Input Field
    prompt = st.text_area("Enter your prompt:", placeholder="Write a blog about AI trends in 2025.")

    # Session management to check for block time and session limits
    check_session_limit()

    # Generate Content Button
    if st.button("Generate Response"):
        if not prompt.strip():
            st.error("Please enter a valid prompt.")
        else:
            try:
                # Generate content using Generative AI
                generated_text = generate_content(prompt)

                # Increment session count
                st.session_state.session_count += 1

                # Display the generated content
                st.subheader("Generated Content:")
                st.write(generated_text)

                # Check for similar content online
                st.subheader("Searching for Similar Content Online:")
                search_results = search_web(generated_text)

                display_search_results(search_results)

            except Exception as e:
                st.error(f"Error generating content: {e}")

    # Display regenerated content if available
    if 'generated_text' in st.session_state:
        st.subheader("Regenerated Content (After Adjustments for Originality):")
        st.write(st.session_state.generated_text)
