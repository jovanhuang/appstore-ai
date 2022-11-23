import logging

import gradio as gr

from .config import config
from .predict import inputs, outputs, predict

if __name__ == "__main__":
    logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s")
    app = gr.Interface(
        predict,
        inputs=inputs,
        outputs=outputs,
        title="{{ cookiecutter.project_name }}",
        description="{{ cookiecutter.short_description }}",
    )
    app.queue().launch(server_port=config.port)
