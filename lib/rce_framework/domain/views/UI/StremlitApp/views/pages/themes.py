Theme = """
            <style>
                /* Basic Dark Theme Adjustments (May need refinement) */
                /* Apply to the main app container */
                .stApp {
                    /* background-color: #1a1a2e; Base color set by theme='dark' is usually sufficient */
                    /* color: white; /* Handled by theme */
                }
                /* Sidebar background */
                [data-testid="stSidebar"] {
                    /* background-color: #0f0f23; /* Try adjusting theme colors first */
                }
                /* Optional: Style specific elements if needed */
                h1, h2, h3, h4, h5, h6 {
                    /* color: #e1e1e1; /* Adjust header colors if needed */
                }
                /* Ensure text input fields are visible */
                .stTextInput input, .stTextArea textarea {
                     color: #333; /* Dark text on light background inside input */
                     background-color: #fff; /* Light background for input */
                }
                 /* Ensure chat input is visible */
                .stChatInput input {
                    color: #333;
                    background-color: #fff;
                }
                /* Increase text size in the sidebar */
                .stSidebar {
                    font-size: 20px;
                }
            </style>
        """