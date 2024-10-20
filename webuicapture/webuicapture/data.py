"""Data classes for data returned by web ui capture extensions."""

from pydantic import (
    BaseModel,
    ValidationInfo,
    HttpUrl,
    Field,
    field_validator,
    model_validator,
    computed_field,
    ConfigDict,
)
from typing import Any
from PIL import Image
from datetime import datetime
from io import BytesIO
import base64
from pathlib import Path


class BBoxNode(BaseModel):
    """Data Representing a web element (bounding box) that has been captured."""

    tag: str  # html tag name
    bbox: tuple[int, int, int, int]
    children: list["BBoxNode"]
    meta: dict[str, Any]

    @field_validator("bbox", mode="before")
    @classmethod
    def validate_bbox(cls, value: Any, info: ValidationInfo):
        """Validator for the bbox field."""
        if len(value) != 4:
            raise ValueError(
                "`bbox` must contain exactly four elements: (x1, y1, x2, y2)"
            )
        if not all(isinstance(x, int) for x in value):
            raise ValueError("`bbox` must contain only integers")

        if value[0] > value[2] or value[1] > value[3]:
            raise ValueError("`bbox` must satisfy x1 < x2 and y1 < y2")

        if any(x < 0 for x in value):
            raise ValueError("`bbox` coordinates must be >= 0")

        if "image_size" not in info.context:
            raise ValueError("Required validation context `image_size` is missing")

        w, h = info.context["image_size"]
        if any(x > w for x in value[0::2]):
            raise ValueError(
                f"`bbox` x coordinates {value[0::2]} must be <= image width {w}"
            )
        if any(x > h for x in value[1::2]):
            raise ValueError(
                f"`bbox` y coordinates {value[1::2]} must be <= image height {h}"
            )
        return tuple(value)

    @field_validator("tag", mode="before")
    @classmethod
    def validate_tag(cls, value: str):
        """Validator for the tag field."""
        if value is None or not isinstance(value, str) or not value.strip():
            raise ValueError("`tag` must be a non-empty string")
        return value


class ImageType:
    """Data representing an image (screenshot) that has been captured."""

    def __init__(self, image_base64: str):
        """Constructor.

        Args:
            image_base64 (str): Base64 encoded image.
        """
        self._pil_image = ImageType.decode_from_base64(image_base64).convert("RGB")

    @property
    def image(self) -> Image:
        """Get image data.

        Returns:
            Image: image data
        """
        return self._pil_image

    def save(self, path: str | Path):
        """Save the image to disk.

        Args:
            path (str | Path): path to save the image to.

        Returns:
            bool: True if the image was saved successfully, False otherwise.
        """
        return self._pil_image.save(Path(path).as_posix())

    @classmethod
    def decode_from_base64(cls, image_base64: str) -> Image:
        """Decode image from base64.

        Args:
            image_base64 (str): Base64 encoded image.

        Returns:
            Image: image data
        """
        image_base64_bytes = image_base64.encode("utf-8")
        return Image.open(BytesIO(base64.b64decode(image_base64_bytes)))

    @classmethod
    def encode_to_base64(cls, image: Image) -> str:
        """Encode image to base64.

        Args:
            image (Image): image data

        Returns:
            str: Base64 encoded image
        """
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    @property
    def size(self) -> tuple[int, int]:
        """Get image size.

        Returns:
            tuple[int, int]: image size (width, height)
        """
        return self._pil_image.size

    def __str__(self) -> str:  # noqa
        return f"Image({self.size})"

    def __repr__(self) -> str:  # noqa
        return str(self)

    # def __get_pydantic_core_schema__(self, schema_generator):
    #     """Provide a JSON schema for the ImageType."""
    #     return core_schema.str_schema()


class CaptureData(BaseModel):
    """Data representing a web ui capture."""

    url: HttpUrl
    timestamp: datetime
    bbox_tree: BBoxNode

    # excluded from the schema, will be saved as a seperate .png file
    image: ImageType = Field(exclude=True)

    # pydantic config options (not part of the schema)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="before")
    def validate_model(cls, values: dict[str, Any], info: ValidationInfo):
        """Validate CaptureData, this will decode the `image` and add the `image_size to the context."""
        # the image needs to be decoded here as it is used in bbox field validators
        values["image"] = ImageType(values["image"])
        info.context["image_size"] = values["image"].size
        return values

    @computed_field
    def image_size(self) -> tuple[int, int]:
        """Get image size.

        Returns:
            tuple[int, int]: image size (width, height)
        """
        return self.image.size

    def save_to_json(self, path: str | Path, filename: str):
        """Save the capture data to disk.

        The data will be saved in two files:
        - `path`/`filename`.json - file containing the capture data (excluding the image).
        - `path`/`filename`.png` - file containing the screenshot.

        Args:
            path (str): path to save the capture data to.
            filename (str): filename to save the capture data to.
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        json_path = (path / filename).with_suffix(".json")
        image_path = (path / filename).with_suffix(".png")

        # write the json data
        with open(json_path, "w") as f:
            f.write(self.model_dump_json(indent=2))
        # write image data
        self.image.save(image_path)


if __name__ == "__main__":
    image = Image.open(
        "C:/Users/brjw/Documents/repos/agent/ui-capture-chrome-extension/dataset/test.png"
    )
    base64_image = ImageType.encode_to_base64(image)
    # decoded_image = ImageType.decode_from_base64(base64_image)
    # decoded_image.show()

    capture_data = CaptureData.model_validate_json(
        '{"image": "%s", "bbox_tree": {"children": [], "bbox": [20, 50, 100, 100], "tag": "div", "meta": {}}, "timestamp": "2024-01-01T00:00:00", "url": "https://example.com"}'  # noqa
        % base64_image,
        context=dict(),
    )
    capture_data.save_to_json("./dataset/", "ok")

    # bbox_tree = BBoxNode.model_validate_json(
    #     '{"children": [{"children": [], "bbox": [20, 50, 100, 100], "tag": "div", "meta": {}}], "bbox": [20, 50, 100, 100], "tag": "div", "meta": {}}',
    #     context=dict(image_size=(1920, 1080)),
    # )

    # print(bbox_tree.model_dump_json(indent=2))
