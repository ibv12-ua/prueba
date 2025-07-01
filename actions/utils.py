def chunk_buttons(buttons, n=3):
            """Splits a list of buttons into chunks of size n."""
            for i in range(0, len(buttons), n):
                yield buttons[i:i+n]