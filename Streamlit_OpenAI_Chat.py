#------------------------- IMPORTS
import streamlit as st
from openai import OpenAI
import os
import re


#------------------------------ Local Quick Keying
# openai_key = "KEY"


#-------------------------- TOM Secrets
# openai_key = st.secrets["openai_key"]


#----------------------------- .env
# openai_key = os.environ.get("openai_key")

from pathlib import Path
import sys


botTitle = "OpenAI Chat"

#These are the avatar settings
userAvatar = None
aiAvatar = None
# userAvatar = ":material/face:" 
# aiAvatar = ":material/neurology:"
# userAvatar = "⌨️" 
# aiAvatar = "🖥️"


#Gifs for Images!
side_bar_image = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3JxaWs4dXJ6OHd6OTluc3R2NXpjMGE3M2dtZ3JnbWN1cHFwczFhNiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/sRFEa8lbeC7zbcIZZR/giphy.gif"
error_image = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcGlqcGxmaHE2ajM3YnBrMGV0dDdwbTF6NXd5aWM2MXJzMWZubWpqayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/273P92MBOqLiU/giphy.gif"


              
#----------------------------------------------------- StreamLit UI

# Session States
st.set_page_config(page_title=botTitle, page_icon=":speech_balloon:",layout="wide")
SYSTEM_PROMPT = ""



#Drop Down To Select what is happening
st.sidebar.image(side_bar_image)


def openai_chat():
    allowed_extensions = [
    "doc", "docx", "html", "json", "md", "pdf", "php","txt"
    ]

    client = OpenAI(api_key=openai_key)
    
    #Prompt Data!
    def get_base_path() -> Path:
        """Returns the directory of the script or the frozen executable."""
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        return Path(__file__).parent

    # Locate prompts folder once
    BASE_PATH = get_base_path()
    PROMPTS_DIR = BASE_PATH / "prompts"

    @st.cache_data(show_spinner=False)
    def load_prompt(name: str) -> str:
        """Load the text of a prompt file (no “.txt” in `name`)."""
        return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")
        
    def clear_systemprompt():
        """Callback to wipe out any existing system prompt."""
        st.session_state.systemprompt = ""
    
    def run_side_bar():
        # — Model Choice —
        if "model_choice" not in st.session_state:
            st.session_state.model_choice = "gpt-4.1-mini"
        st.session_state.model_choice = st.sidebar.selectbox(
            "Model Selection",
            ["gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano","o4-mini"],
            index=["gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano","o4-mini"]
                  .index(st.session_state.model_choice),
        )

        if st.sidebar.button("Clear Conversation", use_container_width=True):
            clear_conversation()

        # — Search Checkbox —
        if "use_search" not in st.session_state:
            st.session_state.use_search = False
        st.session_state.use_search = st.sidebar.checkbox(
            "Use Search", value=st.session_state.use_search
        )

        # — File Uploader for Vector Store —
        uploaded_file = st.sidebar.file_uploader(
            "Upload for File Search", type=allowed_extensions
        )
        if uploaded_file:
            if "vector_store_id" not in st.session_state:
                vector_store = client.vector_stores.create(name=uploaded_file.name)
                client.vector_stores.files.upload_and_poll(
                    vector_store_id=vector_store.id,
                    file=uploaded_file
                )
                client.vector_stores.update(
                    vector_store_id=vector_store.id,
                    expires_after={"anchor": "last_active_at", "days": 1}
                )
                st.session_state.vector_store_id = vector_store.id
                st.sidebar.write("Vector store created!")
        else:
            st.session_state.pop("vector_store_id", None)

        # — System Prompt / Stored Prompts setup —
        if "systemprompt" not in st.session_state:
            st.session_state.systemprompt = ""

        # Ensure we have a flag in session state
        if "use_stored_prompts" not in st.session_state:
            st.session_state.use_stored_prompts = False

        st.sidebar.checkbox(
            "Use Stored Prompts",
            key="use_stored_prompts",
            on_change=clear_systemprompt,
        )
        use_stored = st.session_state.use_stored_prompts

        if use_stored:
            # If folder missing, bail early
            if not PROMPTS_DIR.exists():
                st.sidebar.error(f"Can't find prompts folder at {PROMPTS_DIR}")
                return

            # Populate dropdown from .txt stems
            files = sorted(PROMPTS_DIR.glob("*.txt"))
            names = [f.stem for f in files]
            choice = st.sidebar.selectbox("Choose a stored prompt:", names)

            # Immediately load that file into the session
            st.session_state.systemprompt = load_prompt(choice)
            st.sidebar.write(f"Loaded **{choice}.txt**")

        else:
            # Manual entry; since clear_systemprompt fired on uncheck,
            # session_state.systemprompt is now "".
            st.session_state.systemprompt = st.sidebar.text_area(
                "System Prompt",
                st.session_state.systemprompt,
                height=100,
            )

    def get_open_ai_response(conversation):
        _model = st.session_state["model_choice"]
        _tools = []  
        # Add the web search tool if enabled
        if st.session_state.get("use_search", False): 
            _tools.append({
                "type": "web_search_preview",
                "search_context_size": "low",
            })
    
        # Add the file search tool if vector_store_id is present
        if "vector_store_id" in st.session_state:
            _tools.append({
                "type": "file_search",
                "vector_store_ids": [st.session_state.vector_store_id]
            })
    
        return client.responses.create(
            model=_model,
            input=conversation,
            tools=_tools,
            stream=True  
        )

    def clear_conversation():
        st.session_state.conversation.clear()
        st.toast("Memory Cleared")

    def gpt_chat_loop():
        if "conversation" not in st.session_state:
            st.session_state.conversation = []

        # Display conversation history. For user messages, we show 'display' if available.
        for msg in st.session_state.conversation:
            if msg["role"] in ["user", "assistant"]:
                with st.chat_message(msg["role"]):
                    # Use the 'display' field if it exists (for user messages) or fallback to 'content'.
                    st.write(msg.get("display", msg["content"]))

        # Streamlit's chat input widget for the new question
        user_input = st.chat_input("How can I help you?")
        if user_input:
            # Display only the raw user question in the chat window.
            with st.chat_message("user"):
                st.write(user_input)

            st.session_state.conversation.append({
                            "role": "user",
                            "content": user_input
                        })
            #Add the System Prompt
            sendTo = st.session_state.conversation
            sendTo.insert(0, {"role": "system", "content": st.session_state.systemprompt})
            # Generate the assistant's answer using the conversation without the "display" key
            with st.spinner("Processing...",show_time=True):
                # Create a chat message container for the assistant's response.
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    response = get_open_ai_response(sendTo)
                    answer = ""  # This will accumulate our complete answer.
                    # Iterate through each streamed chunk.
                    for event in response:
                        if event.type == "response.output_text.delta":
                            token = event.delta
                            answer += token
                            # Update the chat message container with the current answer.
                            # You can use write or markdown depending on your content.
                            placeholder.markdown(answer)
                            print(event.delta, end="")
                # Once the complete answer is received, append it to the conversation history.
                st.session_state.conversation.append({
                    "role": "assistant",
                    "content": answer
                })
    run_side_bar()
    gpt_chat_loop()

openai_chat()
