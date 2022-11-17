import os
from datetime import datetime

import gradio as gr
import numpy as np
import tritonclient.grpc as tritongrpc
from scipy.special import softmax
from transformers import XLMRobertaTokenizer


def loadModel(
    model_name="zst",
    model_version="1",
    url="127.0.0.1:8001",
    loading="POLLING",
):
    # establish connection to triton
    triton_client = tritongrpc.InferenceServerClient(url=url, verbose=VERBOSE)
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PASSED: Connection'
    )

    # load model in triton, not needed if mode = 'polling'
    if loading == "EXPLICIT":
        triton_client.load_model(model_name)
    if not triton_client.is_model_ready(model_name):
        print(
            f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] FAILED: Load Model'
        )
    else:
        print(
            f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PASSED: Load Model'
        )

    # get model data
    model_metadata = triton_client.get_model_metadata(
        model_name=model_name, model_version=model_version
    )
    model_config = triton_client.get_model_config(
        model_name=model_name, model_version=model_version
    )
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] CONFIG: {model_config}'
    )
    return triton_client


def unloadModel(triton_client, model_name="zst"):
    # unload model from triton server
    triton_client.unload_model(model_name)
    if triton_client.is_model_ready(model_name):
        print(
            f'\n[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] FAILED: Unload Model'
        )
    else:
        print(
            f'\n[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PASSED : Unload Model'
        )


def run_inference(
    triton_client,
    premise="",
    topic="",
    model_name="zst",
    model_version="1",
):

    topic = topic
    print(
        f'\n[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PREMISE: {premise}'
    )
    print(f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] TOPIC: {topic}')

    # tokenize input
    input_ids = R_tokenizer.encode(
        premise, topic, max_length=256, truncation=True, padding="max_length"
    )
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PASSED: Tokenize'
    )

    # format inputs
    input_ids = np.array(input_ids, dtype=np.int32)
    mask = input_ids != 1
    mask = np.array(mask, dtype=np.int32)
    mask = mask.reshape(1, 256)
    input_ids = input_ids.reshape(1, 256)

    # insert inputs and output(s)
    input0 = tritongrpc.InferInput(input_name[0], (1, 256), "INT32")
    input0.set_data_from_numpy(input_ids)
    input1 = tritongrpc.InferInput(input_name[1], (1, 256), "INT32")
    input1.set_data_from_numpy(mask)
    output = tritongrpc.InferRequestedOutput(output_name)
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PASSED: Inputs/Outputs'
    )

    # send inputs for inference and recieve output(s)
    response = triton_client.infer(
        model_name,
        model_version=model_version,
        inputs=[input0, input1],
        outputs=[output],
    )
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PASSED: Inference'
    )

    # format output(s)
    logits = response.as_numpy("output__0")
    logits = np.asarray(logits, dtype=np.float32)
    entail_contradiction_logits = logits[:, [0, 2]]
    probs = softmax(entail_contradiction_logits)
    true_prob = probs[:, 1].item() * 100
    false_prob = probs[:, 0].item() * 100
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PASSED: Probability\n'
    )

    # display outputs
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PREDICTION: Label has {true_prob:0.2f}% of being true'
    )
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] PREDICTION: Label has {false_prob:0.2f}% of being false'
    )

    return true_prob


try:
    # load tokeniser
    R_tokenizer = XLMRobertaTokenizer.from_pretrained(
        "joeddav/xlm-roberta-large-xnli"
    )
    VERBOSE = False
    # set up input for triton
    input_name = ["input__0", "input__1"]
    output_name = "output__0"
    # get variables from env pass in Dockerfile
    MODEL_NAME = os.environ.get("MODEL_NAME", "xlm_roberta_zsl")
    MODEL_VERSION = os.environ.get("MODEL_VERSION", "1")
    TRITON_HOSTNAME = os.environ.get("TRITON_HOSTNAME", "172.20.0.4")
    TRITON_PORT = str(os.environ.get("TRITON_PORT", "8001"))
    TRITON_URL = f"{TRITON_HOSTNAME}:{TRITON_PORT}"
    TRITON_MODE = os.environ.get("TRITON_MODE", "EXPLICIT")
    HOSTNAME = os.environ.get("HOSTNAME", "127.0.0.1")
    # get Triton client and load model in Triton
    client = loadModel(MODEL_NAME, MODEL_VERSION, TRITON_URL, TRITON_MODE)

    def question_answer(premise, topic):
        # get content from Gradio frontend
        splitTopic = list(filter(None, topic.split(",")))
        list_output = []
        styledOutput = ""
        for x in splitTopic:
            # run NLI inference in Triton server and return correct output
            output = run_inference(
                client, premise, x.strip(), MODEL_NAME, MODEL_VERSION
            )
            list_output.append([x, output])
        # sort by truth confidence percentage
        list_output = sorted(list_output, key=lambda x: x[1], reverse=True)
        # format outputs for display
        for i in list_output:
            styledOutput += f"{i[0].strip()} ({round(i[1],2)}%)\n"
        return styledOutput.strip()

    with gr.Blocks() as demo:
        # styling for Gradio frontend
        premiseBox = gr.Textbox(
            placeholder="Text to classify...", label="Zero Shot Classification"
        )
        topicBox = gr.Textbox(
            placeholder="Possible class names...",
            label="Possible class names (comma-separated)",
        )

        comp_btn = gr.Button("Compute")

        output = gr.Textbox(
            label="Probabilities",
            placeholder="<Label> (<Probability of being true>)",
        )
        # call function that sends inputs for inference and formats outputs for  display
        comp_btn.click(
            fn=question_answer, inputs=[premiseBox, topicBox], outputs=output
        )

    if __name__ == "__main__":
        # launch Gradio frontend
        demo.launch(server_port=int(os.environ.get("PORT", 8080)))
except:
    # catch for errors and unload model in Triton
    # NOTE: This doesn't really work very well, some issues with SciPy/other packages causes complete crash when keyboard interrupting
    unloadModel(client, MODEL_NAME)
    print(
        f'[{(datetime.now()).strftime("%d-%m-%Y %H:%M:%S")}] Exited Application'
    )
