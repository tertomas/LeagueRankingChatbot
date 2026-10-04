import streamlit as st
from chatbot import ask_question

# Basic title
st.title("Guardian League Ranking Chatbot")

# User form title with an input and a submit button
with st.form("question_form"):
    question = st.text_input(
        "Ask a question about the UK university rankings:"
    )
    submitted = st.form_submit_button("Ask")

# Action on form submission or pressing enter
if submitted:
    if question:
        try:
            sql, result, status = ask_question(question)

            # Question does not match the data
            if status == "CANNOT_ANSWER":
                st.warning("I can't answer this question using the available database.")

            # Explain type question
            elif status == "EXPLANATION":
                st.subheader("Explanation")
                st.write(result)

            # SQL type question
            else:
                with st.expander("Show generated SQL"):
                    st.code(sql, language="sql")

                if status == "NO_DATA":
                    st.warning("I couldn't find any data matching your question."                )

                else:
                    st.subheader("Answer")
                    st.dataframe(result)

        except Exception as e:
            st.error("Oops! Something went wrong while processing your request.")            
            with st.expander("Error details (for debugging)"):
                st.write(str(e))

    else:
        st.warning("Please enter a question.")