"""Utility for visualising UI with the element tree."""

import gradio as gr
import numpy as np
from pathlib import Path
from functools import partial
from PIL import Image
import json
import cv2

# from gradio.components.base import Component, server
# from gradio_client.documentation import document


# TODO explorer to get folder we want... currently just using a textbox
# @document()
# class DirectoryExplorer(gr.FileExplorer):
#     def __init__(self, root_dir: str, **kwargs):
#         super().__init__(root_dir=root_dir, file_count="multiple", **kwargs)

#     @server
#     def ls(self, subdirectory: list[str] | None = None) -> list[dict[str, str]] | None:
#         result = super().ls(subdirectory)
#         result = list(filter(lambda x: x["type"] == "directory", result))
#         return result


DIRECTORY = Path("~/").expanduser().resolve()
FILES = []
INDEX = 0


def load_annotated_image(image_file: Path, ann_file: Path):
    # image_file = image_file.with_name("test").with_suffix(".png")
    # ann_file = ann_file.with_name("test").with_suffix(".json")

    def get_bboxes(node):
        yield (node["bbox"], node["tag"])
        for child in node["children"]:
            yield from get_bboxes(child)

    image = Image.open(image_file.as_posix())
    with open(ann_file.with_suffix(".json").as_posix()) as f:
        annotation = get_bboxes(json.load(f)["bbox_tree"])

    image = np.array(image)
    for bbox, tag in annotation:
        cv2.rectangle(image, bbox[:2], bbox[2:], (255, 0, 0), 2)
        # cv2.putText(image, tag, (bbox[0], bbox[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    return image, []  # annotation
    # return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8), []


def _next_image():
    # TODO use a class to encapsulate all this garbage
    files = list(DIRECTORY.glob("*.png"))
    global INDEX
    if len(files) > 0:
        INDEX = (INDEX + 1) % len(files)
        return load_annotated_image(files[INDEX], files[INDEX].with_suffix(".csv"))
    return None


def _prev_image():
    global INDEX, FILES
    if len(FILES) > 0:
        INDEX = (INDEX - 1) % len(FILES)
        return load_annotated_image(FILES[INDEX], FILES[INDEX].with_suffix(".csv"))
    return None


def select_directory(directory, glob="*.png"):
    global DIRECTORY, FILES, INDEX
    directory = Path(directory).expanduser()
    print(directory, directory.exists(), directory.is_dir())
    if directory.exists() and directory.is_dir():
        # list files in the directory
        DIRECTORY = directory.expanduser().resolve()
        FILES = list(directory.glob(glob))
        INDEX = 0
    return None


DEFAULT_DIRECTORY = (
    Path("~/Documents/repos/agent/ui-capture-chrome-extension/dataset")
    .expanduser()
    .resolve()
)
select_directory(DEFAULT_DIRECTORY)

with gr.Blocks() as demo:
    annotated_image = gr.AnnotatedImage()
    dir_explorer = gr.Textbox(
        show_label=False,
        placeholder="Enter directory...",
        value=DEFAULT_DIRECTORY.as_posix(),
    )
    dir_explorer.change(
        fn=partial(select_directory, glob="*.png"),
        inputs=dir_explorer,
    )

    with gr.Row():
        btn_prev = gr.Button("Prev")
        btn_next = gr.Button("Next")
        btn_next.click(fn=_next_image, inputs=[], outputs=annotated_image)

    # # def overlay_boxes(self, directory):
    # #     # annotations = []
    # #     # for _, (x, y, width, height, color) in boxes.iterrows():
    # #     #     annotations.append(((x, y, x + width, y + height), color))
    # #     img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    # #     return img, []

    # def launch(self):
    #     self.iface.launch()

demo.launch()
