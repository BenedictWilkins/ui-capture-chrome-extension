"""FastAPI server for capturing web UI data.

This is the end point for browser extensions.
It must be running if the extension is going to be capturing data.

Run with:
```
uvicorn webuicapture.serve:app --reload --port 7659
```
after installing webuicapture with pip.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import asyncio
import uuid
import gradio as gr
import json
import numpy as np
import cv2

from .data import CaptureData

app = FastAPI()

# only allow requests from localhost TODO
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost", "http://127.0.0.1"],  # Allow only localhost
    allow_origins=["*"],  # Allow all origins, TODO this may be a security risk...
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

state = asyncio.Queue(maxsize=1)


@app.post("/upload")
async def upload_data(request: Request):
    """Endpoint for uploading capture data from browser extensions."""
    # The raw request is needed here to prevent fastapi validation errors... (some issue with json serialization schema)
    try:
        print("UPLOADED IMAGE")
        data = CaptureData.model_validate_json(await request.body(), context={})
        image_path, bbox_layout_path = data.save_to_json(
            "./dataset/", str(uuid.uuid4())
        )
        await state.put(
            {"image_path": image_path, "bbox_layout_path": bbox_layout_path}
        )
        return {}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
def home():
    """Home page."""
    return {"message": "This is your main app"}


# ========= ========== ========= #
# ========= gradio app ========= #
# ========= ========== ========= #

# def gr_update(image_path: str, bbox_layout_path: str):
#     image_path = Path(image_path)
#     bbox_layout_path = Path(bbox_layout_path)
#     img = Image.open(image_path.resolve().as_posix())
#     print("UPDATE!")
#     image.value = img
#     print(image.value)
#     return None


async def stream():
    """Streams the latest image that was captured."""

    def get_bboxes(node):
        yield (node["bbox"], node["tag"])
        for child in node["children"]:
            yield from get_bboxes(child)

    while True:
        _data = await state.get()
        image_path = _data["image_path"]
        bbox_layout_path = _data["bbox_layout_path"]
        with open(bbox_layout_path.resolve().as_posix()) as f:
            annotation = get_bboxes(json.load(f)["bbox_tree"])

        img = Image.open(image_path.resolve().as_posix())
        img = np.array(img)
        for bbox, tag in annotation:
            cv2.rectangle(img, bbox[:2], bbox[2:], (255, 0, 0), 2)

        yield img


# async def stream_test(text: gr.Textbox):
#     for i in range(10):
#         await asyncio.sleep(1)


with gr.Blocks() as demo:
    with gr.Row():
        # text = gr.Textbox(interactive=False)
        image = gr.Image(interactive=False)
        demo.load(stream, outputs=image)
        # state.value = dict(image_path="test", bbox_layout_path="test")
        # print("???", state.value)

        # btn = gr.Button("test")
        # btn.click(stream, inputs=image, outputs=image)
        #
        # btn.click(stream_test, inputs=text, outputs=text)
        # btn.click(
        #     partial(
        #         gr_update,
        #         image_path="dataset/bad-slack.png",
        #         bbox_layout_path="dataset/bad-slack.json",
        #     )
        # )


# ========= ========== ========= #


# io = gr.Interface(lambda x: "Hello, " + x + "!", "textbox", "textbox")
app = gr.mount_gradio_app(app, demo, path="/gradio")


# def launch_gradio_app():
#     """Launch a gradio app to visualise the dataset."""

#     def greet(name):
#         return f"Hello {name}!"

#     gr.Interface(fn=greet, inputs="text", outputs="text").launch(share=True)


# if __name__ == "__main__":
#     print("GRADIO APP STARTED")
#     threading.Thread(target=launch_gradio_app, daemon=True).start()


# class PingMessage(BaseModel):  # noqa
#     message: str

# @app.post("/ping")
# async def ping(request: Request, message: PingMessage):
#     """Endpoint for testing server connection."""
#     origin = request.headers.get("origin")
#     print(f"{time.time()}, PING: {message}, origin: {origin}")
#     return {"message": message}
