from openai import OpenAI


def ask_gpt(prompt, raw):
    client = OpenAI()

    Prompt = (
        "this is a python code :\n"
        + "```python\n"
        + raw
        + "```\n"
        + prompt
        + "Format your response by: Showing the whole modified code. No explanation is required. Only code."
    )

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": Prompt},
        ],
    )

    answer = response.choices[0].message.content
    return answer


def extract_command(gptCommand):
    blocks = []
    temp = ""
    writing = False

    for line in gptCommand.splitlines():
        if line == "```":
            writing = False
            blocks.append(temp)
            temp = ""

        if writing:
            temp += line
            temp += "\n"

        if line == "```python":
            writing = True

    return blocks


def save_as(content, path):
    # use at the end of replace_2 as save_as(end_result, "file_path")
    with open(path, "w") as file:
        file.write(content)


import pyarrow as pa

from dora import DoraStatus


class Operator:
    """
    Infering object from images
    """

    def on_event(
        self,
        dora_event,
        send_output,
    ) -> DoraStatus:
        if dora_event["type"] == "INPUT":
            input = dora_event["value"][0].as_py()
            with open(input["path"], "r", encoding="utf8") as f:
                raw = f.read()
            print("--- Asking chatGPT ", flush=True)
            response = ask_gpt(input["query"], raw)
            blocks = extract_command(response)
            print(response, flush=True)
            print(blocks[0], input["path"], flush=True)
            save_as(blocks[0], input["path"])

        return DoraStatus.CONTINUE
