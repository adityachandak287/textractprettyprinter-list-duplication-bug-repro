import json
import logging
import os
import sys

import boto3
from textractcaller import Textract_Features, call_textract
from textractprettyprinter.t_pretty_print import get_text_from_layout_json
import glob

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
)

logger = logging.getLogger("script")

session = boto3.Session(region_name=os.environ.get("AWS_REGION", "ap-south-1"))
textract_client = session.client("textract")

def replace_file_extension(file: str, target_ext: str) -> str:
    """Replace the file extension of given file with the target extension."""
    if not target_ext.startswith("."):
        target_ext = "." + target_ext

    root, _ = os.path.splitext(file)
    return root + target_ext

def main(pdf_file: str) -> None:
    textract_output_file = replace_file_extension(pdf_file, ".json")
    text_output_file = replace_file_extension(pdf_file, ".txt")

    logger.info("Processing file %s", pdf_file)

    if not os.path.exists(textract_output_file):
        logger.warning(
            "Did not find textract JSON output at %s, generating output might take a while...",
            textract_output_file,
        )

        logger.debug("Reading file %s as bytes", pdf_file)
        with open(pdf_file, "rb") as sample_file:
            pdf_file_bytes = bytearray(sample_file.read())

        textract_json = call_textract(
            input_document=pdf_file_bytes,
            features=[Textract_Features.LAYOUT, Textract_Features.TABLES],
            boto3_textract_client=textract_client,
            force_async_api=False,
        )
        with open(textract_output_file, "w") as toj_file:
            json.dump(fp=toj_file, obj=textract_json, ensure_ascii=False)
            logger.info("Wrote out textract output json to %s", toj_file.name)
    else:
        with open(textract_output_file, "r") as toj_file:
            textract_json = json.load(fp=toj_file)
            logger.info("Read in textract output json from %s", toj_file.name)

    layout = get_text_from_layout_json(
        textract_json=textract_json,
        generate_markdown=False,
        exclude_figure_text=False,
    )

    full_doc_output = "\n---\n".join([layout[page_num] for page_num in layout])

    logger.info(full_doc_output)

    with open(text_output_file, "w") as outfile:
        outfile.write(full_doc_output)
        logger.info("Wrote out text contents to %s", outfile.name)


if __name__ == "__main__":
    for pdf_file in glob.glob("./data/*.pdf"):
        main(pdf_file)
