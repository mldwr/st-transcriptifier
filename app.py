from fastapi import FastAPI, Body
import streamlit as st

app = FastAPI()

@app.post("/letter_count")
async def letter_count(text: str = Body(..., embed=True)):
    return {"letter_count": len(text)}

st.title("Letter Counter")

text = st.text_input("Enter text")
if text:
    result = len(text)
    st.write("Number of letters: ", result)

