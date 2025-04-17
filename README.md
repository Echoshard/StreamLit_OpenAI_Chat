# StreamLit OpenAI Chat

This is a streamlit app using the new Responses API allowing for search and chat with your documents for example PDFS.

### Supports

- OpenAI Search (some models supported)
- File Upload (Chat with your documents)

Uploaded files expire after 24 hours to save space, If you want persistant storage please look assistants https://github.com/Echoshard/Streamlit_OpenAI_Assistants

### Configuration

When running on Streamlit cloud this can be configured with just your API key.

```
#-------------------------- TOM Secrets
openai_key = st.secrets["openai_key"]

```

Additionally there are settings for plain text and setting a .env. Uncomment and comment the ones needed.

```
#------------------------------ Local Quick Keying
# openai_key = ""


#----------------------------- .env
# openai_key = os.environ.get("openai_key")
```

## Local Running
- Download this repo and set your keys up
```
 pip install -r requirements.txt
```

```
 python -m streamlit run PATH:\\OpenAI_Streamlit_Assistants.py
```

# Hosting your App:
The fastest way to run this using streamlit using https://streamlit.io/gallery. 
Another site for doing this is https://render.com/


### Notes:

Image upload will be added another time currently it complicates the code and I have the assistants or gemini that can handle chat with images.
