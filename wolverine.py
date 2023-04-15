import difflib
import fire
import json
import os
import shutil
import subprocess
import sys
import openai
from termcolor import cprint
from dotenv import load_dotenv


# Set up the OpenAI API
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-4")


with open("prompt.txt") as f:
    SYSTEM_PROMPT = f.read()


def run_script(script_name, script_args):
    script_args = [str(arg) for arg in script_args]
    try:
        result = subprocess.check_output(
            [sys.executable, script_name, *script_args], stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8"), e.returncode
    return result.decode("utf-8"), 0

def run_test(test_name):
    try:
        result = subprocess.check_output(["pytest", test_name], stderr=subprocess.STDOUT)
        cprint(result, "green")
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8"), e.returncode
    return result.decode("utf-8", 0)

def json_validated_response(model, messages):
    """
    This function is needed because the API can return a non-json response.
    This will run recursively until a valid json response is returned.
    todo: might want to stop after a certain number of retries
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.5,
    )
    messages.append(response.choices[0].message)
    content = response.choices[0].message.content
    cprint(f"{messages}", "yellow")
    # see if json can be parsed
    try:
        json_start_index = content.index(
            "["
        )  # find the starting position of the JSON data
        json_data = content[
            json_start_index:
        ]  # extract the JSON data from the response string
        json_response = json.loads(json_data)
    except (json.decoder.JSONDecodeError, ValueError) as e:
        cprint(f"{e}. Re-running the query.", "red")
        # debug
        cprint(f"\nGPT RESPONSE:\n\n{content}\n\n", "yellow")
        # append a user message that says the json is invalid
        messages.append(
            {
                "role": "user",
                "content": "Your response could not be parsed by json.loads. Please restate your last message as pure JSON.",
            }
        )
        return {
            "is_valid": False,
            "json_response": None
        }
    except Exception as e:
        cprint(f"Unknown error: {e}", "red")
        cprint(f"\nGPT RESPONSE:\n\n{content}\n\n", "yellow")
        raise e
    return {
        "is_valid": True,
        "json_response": json_response
    }


def send_error_to_gpt(file_path, args, error_message, model=DEFAULT_MODEL):
    with open(file_path, "r") as f:
        file_lines = f.readlines()

    file_with_lines = []
    for i, line in enumerate(file_lines):
        file_with_lines.append(str(i + 1) + ": " + line)
    file_with_lines = "".join(file_with_lines)

    prompt = (
        "Here is the script that needs fixing:\n\n"
        f"{file_with_lines}\n\n"
        "Here is the test result:\n\n"
        f"{error_message}\n"
        "Please provide your suggested changes, and remember to stick to the "
        "exact format as described above."
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]
    cprint(messages, "yellow")
    response_attempt = json_validated_response(model, messages)

    if response_attempt["is_valid"]:
        return response_attempt["json_response"]

    return False


def apply_changes(file_path, changes: list):
    """
    Pass changes as loaded json (list of dicts)
    """
    with open(file_path, "r") as f:
        original_file_lines = f.readlines()

    # Filter out explanation elements
    operation_changes = [change for change in changes if "operation" in change]
    explanations = [
        change["explanation"] for change in changes if "explanation" in change
    ]

    # Sort the changes in reverse line order
    operation_changes.sort(key=lambda x: x["line"], reverse=True)

    file_lines = original_file_lines.copy()
    for change in operation_changes:
        operation = change["operation"]
        line = change["line"]
        content = change["content"]

        if operation == "Replace":
            file_lines[line - 1] = content + "\n"
        elif operation == "Delete":
            del file_lines[line - 1]
        elif operation == "InsertAfter":
            file_lines.insert(line, content + "\n")

    with open(file_path, "w") as f:
        f.writelines(file_lines)

    # Print explanations
    cprint("Explanations:", "blue")
    for explanation in explanations:
        cprint(f"- {explanation}", "blue")

    # Show the diff
    print("\nChanges:")
    diff = difflib.unified_diff(original_file_lines, file_lines, lineterm="")
    for line in diff:
        if line.startswith("+"):
            cprint(line, "green", end="")
        elif line.startswith("-"):
            cprint(line, "red", end="")
        else:
            print(line, end="")


def main(script_name, test_name, retry_limit, revert=False, model=DEFAULT_MODEL):
    if revert:
        backup_file = script_name + ".bak"
        if os.path.exists(backup_file):
            shutil.copy(backup_file, script_name)
            print(f"Reverted changes to {script_name}")
            sys.exit(0)
        else:
            print(f"No backup file found for {script_name}")
            sys.exit(1)

    # Make a backup of the original script
    shutil.copy(script_name, script_name + ".bak")

    tried_count = 0
    returncode = 1
    while tried_count < int(retry_limit) and returncode != 0:
        cprint("===========================", "red")
        cprint(f"attempt: {tried_count}", "red")
        cprint("===========================", "red")
        tried_count += 1
    
        output, returncode = run_test(test_name)

        if returncode == 0:
            cprint("Tests passed", "blue")
            print("Output:", output)
            break

        else:
            cprint("Test failed. Trying to fix...", "blue")
            print("Output:", output)

            json_response = send_error_to_gpt(
                file_path=script_name,
                args=[],
                error_message=output,
                model=model,
            )

            if json_response: 
                apply_changes(script_name, json_response)
                cprint("Changes applied. Rerunning...", "blue")
                



if __name__ == "__main__":
    fire.Fire(main)
