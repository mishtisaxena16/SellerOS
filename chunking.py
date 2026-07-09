import re

def clean_text(text):

    text = text.replace("\r\n", "\n")

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def semantic_chunk(
    text,
    max_chunk_size=1000
):

    paragraphs = re.split(
        r"\n\s*\n",
        text
    )

    chunks = []
    current = []

    for para in paragraphs:

        current_text = "\n\n".join(current)

        if len(current_text) + len(para) + 2 <= max_chunk_size:

            current.append(para)

        else:

            if current:

                chunks.append(
                    "\n\n".join(current)
                )

                # Keep the last paragraph as overlap
                current = [current[-1], para]

            else:

                current = [para]

    if current:

        chunks.append(
            "\n\n".join(current)
        )

    return chunks