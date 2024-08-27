import json
import logging
import os
import sys

import boto3
from textractcaller import Textract_Features, call_textract
from textractprettyprinter.t_pretty_print import get_text_from_layout_json

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
)

logger = logging.getLogger("script")

session = boto3.Session(region_name=os.environ.get("AWS_REGION", "ap-south-1"))
textract_client = session.client("textract")

PDF_FILE = "./data/textract-test-document.pdf"
TEXTRACT_OUTPUT_FILE = "./data/textract-test-document.json"
TEXT_OUTPUT_FILE = "./data/output-textract-test-document.txt"


def main() -> None:
    logger.debug("Reading file %s as bytes", PDF_FILE)
    with open(PDF_FILE, "rb") as sample_file:
        pdf_file_bytes = bytearray(sample_file.read())

    if not os.path.exists(TEXTRACT_OUTPUT_FILE):
        logger.warning(
            "Did not find textract JSON output at %s, generating output might take a while...",
            TEXTRACT_OUTPUT_FILE,
        )
        textract_json = call_textract(
            input_document=pdf_file_bytes,
            features=[Textract_Features.LAYOUT, Textract_Features.TABLES],
            boto3_textract_client=textract_client,
            force_async_api=False,
        )
        with open(TEXTRACT_OUTPUT_FILE, "w") as toj_file:
            json.dump(fp=toj_file, obj=textract_json, ensure_ascii=False)
            logger.info("Wrote out textract output json to %s", toj_file.name)
    else:
        with open(TEXTRACT_OUTPUT_FILE, "r") as toj_file:
            textract_json = json.load(fp=toj_file)
            logger.info("Read in textract output json from %s", toj_file.name)

    layout = get_text_from_layout_json(
        textract_json=textract_json,
        generate_markdown=False,
        exclude_figure_text=False,
    )

    full_doc_output = "\n---\n".join([layout[page_num] for page_num in layout])
    # for page_num in layout:
    #     full_doc_output += layout[page_num]

    logger.info(full_doc_output)

    with open(TEXT_OUTPUT_FILE, "w") as outfile:
        outfile.write(full_doc_output)
        logger.info("Wrote out text contents to %s", outfile.name)


if __name__ == "__main__":
    main()
