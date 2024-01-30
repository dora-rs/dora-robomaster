from dora import DoraStatus
import pylcs
import textwrap
import pandas as pd
import os
import pyarrow as pa
import numpy as np
from ctransformers import AutoModelForCausalLM


def search_most_simlar_line(text, searched_line):
    lines = text.split("\n")
    values = []

    for line in lines:
        values.append(pylcs.edit_distance(line, searched_line))
    output = lines[np.array(values).argmin()]
    return output


def strip_indentation(code_block):
    # Use textwrap.dedent to strip common leading whitespace
    dedented_code = textwrap.dedent(code_block)

    return dedented_code


def replace_code_with_indentation(original_code, replacement_code):
    # Split the original code into lines
    lines = original_code.splitlines()

    # Preserve the indentation of the first line
    indentation = lines[0][: len(lines[0]) - len(lines[0].lstrip())]

    # Create a new list of lines with the replacement code and preserved indentation
    new_code_lines = indentation + replacement_code

    return new_code_lines


def replace_source_code(source_code, gen_replacement):
    initial = search_most_simlar_line(source_code, gen_replacement)
    print("Initial source code: %s" % initial)
    replacement = strip_indentation(
        gen_replacement.replace("```python\n", "")
        .replace("\n```", "")
        .replace("\n", "")
    )
    intermediate_result = replace_code_with_indentation(initial, replacement)
    end_result = source_code.replace(initial, intermediate_result)
    return end_result


def save_as(content, path):
    # use at the end of replace_2 as save_as(end_result, "file_path")
    with open(path, "w") as file:
        file.write(content)


class Operator:
    def __init__(self):
        # Load tokenizer
        self.llm = AutoModelForCausalLM.from_pretrained(
            "TheBloke/OpenHermes-2.5-Mistral-7B-GGUF",
            model_file="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
            model_type="mistral",
            gpu_layers=50,
        )

    def on_event(
        self,
        dora_event,
        send_output,
    ) -> DoraStatus:
        if dora_event["type"] == "INPUT":
            input = dora_event["value"][0].as_py()

            prompt = f"{input['raw']} \n {input['query']}.  "
            output = self.ask_mistral(
                "You're a code expert. Respond with only one line of code that modify a constant variable. Keep the uppercase.",
                prompt,
            )
            source_code = replace_source_code(input["raw"], output)
            save_as(source_code, input["path"])
        return DoraStatus.CONTINUE

    def ask_mistral(self, system_message, prompt):
        prompt_template = f"""<|im_start|>system
        {system_message}<|im_end|>
        <|im_start|>user
        {prompt}<|im_end|>
        <|im_start|>assistant
        """

        # Generate output
        outputs = self.llm(
            prompt_template,
        )
        # Get the tokens from the output, decode them, print them

        # Get text between im_start and im_end
        return outputs.split("<|im_end|>")[0]


if __name__ == "__main__":
    op = Operator()

    # Path to the current file
    current_file_path = __file__

    # Directory of the current file
    current_directory = os.path.dirname(current_file_path)

    path = current_directory + "/planning_op.py"
    with open(path, "r", encoding="utf8") as f:
        raw = f.read()

    op.on_event(
        {
            "type": "INPUT",
            "id": "tick",
            "value": pa.array(
                [
                    {
                        "raw": raw[:400],
                        "path": path,
                        "query": "Set gimbal yaw to 20",
                    }
                ]
            ),
            "metadata": [],
        },
        print,
    )
