# Wolverine

## About

Prototype to let wolverine work off of pytest results.
I don't have a GPT-4 API key yet, so I tested this using GPT 3.5

This PROTOTYPE branch drastically changed the existing interface. I'm planning to put in smaller PRs later that preserves the original interface. This is just a proof of concept.

Give your python scripts regenerative healing abilities!

Run your scripts with Wolverine and when they crash, GPT-4 edits them and explains what went wrong. Even if you have many bugs it will repeatedly rerun until it's fixed.

For a quick demonstration see my [demo video on twitter](https://twitter.com/bio_bootloader/status/1636880208304431104).

## Setup

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.sample .env

Add your openAI api key to `.env`

_warning!_ By default wolverine uses GPT-4 ~~and may make many repeated calls to the api.~~

## Example Usage

To run with gpt-4 (the default, tested option) and retry up to 5 times:

    python wolverine.py buggy_script.py test_buggy_script.py 5
    
essentially, run 

    python wolverine.py <script.py> <test_file.py> <retry_limit>
    
You can also run with other models, but be warned they may not adhere to the edit format as well:

    python wolverine.py --model=gpt-3.5-turbo wolverine.py buggy_script.py test_buggy_script.py 5

If you want to use GPT-3.5 by default instead of GPT-4 uncomment the default model line in `.env`:

    DEFAULT_MODEL=gpt-3.5-turbo

## Future Plans

(for the pytest proof of concept)
- iterate on the prompt format to coax better result. Should we manipulate the test output somehow?
- add more buggy files and tests
- add a test mode that doesn't actually make calls, but shows an example of what the back and forth message would look like
- gracefully integrate this PoC instead of completely changing the interface.

