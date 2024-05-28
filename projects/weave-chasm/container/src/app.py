import logging
from typing import Any, cast

from eth_abi import decode, encode  # type: ignore
from infernet_ml.utils.service_models import InfernetInput, InfernetInputSource
from infernet_ml.workflows.inference.css_inference_workflow import CSSInferenceWorkflow
from quart import Quart, request

log = logging.getLogger(__name__)


def create_app() -> Quart:
    app = Quart(__name__)

    prompt_workflow = CSSInferenceWorkflow(provider="CHASMNET", endpoint="prompt")
    workflows_workflow = CSSInferenceWorkflow(provider="CHASMNET", endpoint="workflows")

    prompt_workflow.setup()
    workflows_workflow.setup()

    @app.route("/")
    def index() -> str:
        """
        Utility endpoint to check if the service is running.
        """
        return "Chasm.net Example Program"

    @app.route("/service_output", methods=["POST"])
    async def inference() -> dict[str, Any]:
        req_data = await request.get_json()
        """
        InfernetInput has the format:
            source: (0 on-chain, 1 off-chain)
            data: dict[str, Any]
        """
        infernet_input: InfernetInput = InfernetInput(**req_data)

        if infernet_input.source == InfernetInputSource.OFFCHAIN:
            endpoint_id = cast(dict[str, Any], infernet_input.data).get("endpoint_id")
            body = cast(dict[str, Any], infernet_input.data).get("body")
        else:
            # On-chain requests are sent as a generalized hex-string which we will
            # decode to the appropriate format.
            # Note: haven't tested to see the input hex yet.
            (endpoint_id, body) = decode(
                ["string", "string"], bytes.fromhex(cast(str, infernet_input.data))
            )

        if cast(dict[str, Any], infernet_input.data).get("endpoint") == "prompt":
            result: dict[str, Any] = prompt_workflow.inference(
                {
                    "model": "",
                    "params": body,
                }
            )
        else:
            result: dict[str, Any] = workflows_workflow.inference(
                {
                    "model": "",
                    "params": body,
                }
            )

        if infernet_input.source == InfernetInputSource.OFFCHAIN:
            """
            In case of an off-chain request, the result is returned as is.
            """
            return {"message": result}
        else:
            """
            In case of an on-chain request, the result is returned in the format:
            {
                "raw_input": str,
                "processed_input": str,
                "raw_output": str,
                "processed_output": str,
                "proof": str,
            }
            refer to: https://docs.ritual.net/infernet/node/containers for more info.
            """
            return {
                "raw_input": "",
                "processed_input": "",
                "raw_output": encode(["string"], [result]).hex(),
                "processed_output": "",
                "proof": "",
            }

    return app


if __name__ == "__main__":
    """
    Utility to run the app locally. For development purposes only.
    """
    create_app().run(port=3000)
