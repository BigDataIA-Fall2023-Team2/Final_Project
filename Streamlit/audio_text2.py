import streamlit as st
from streamlit_mic_recorder import mic_recorder, speech_to_text

# Function to handle speech-to-text conversion
def handle_speech_to_text():
    state = st.session_state

    # Initialize session state for storing the latest received text
    if 'latest_text' not in state:
        state.latest_text = None

    c1, c2 = st.columns(2)
    with c1:
        st.write("Convert speech to text:")

    # Start recording and convert speech to text
    with c2:
        text = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT', )
    # Store the latest received text in the session state
    if text:       
        state.latest_text = text

# Example usage
handle_speech_to_text()

# Display the latest received text
if st.session_state.latest_text:
    st.text(st.session_state.latest_text)
