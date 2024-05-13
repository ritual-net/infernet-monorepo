from test_library.web3 import deploy_smart_contracts
from dotenv import load_dotenv
import os

load_dotenv()

SERVICE_NAME = "css_inference_service"
env_vars = {
    "PERPLEXITYAI_API_KEY": os.environ["PERPLEXITYAI_API_KEY"],
    "GOOSEAI_API_KEY": os.environ["GOOSEAI_API_KEY"],
    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
}
private_key = os.environ["PRIVATE_KEY"]
rpc_url = os.environ["RPC_URL"]
coordinator_address = os.environ["COORDINATOR_ADDRESS"]

if __name__ == "__main__":
    # deploy_node(
    #     SERVICE_NAME,
    #     env_vars=env_vars,
    #     private_key=private_key,
    #     rpc_url=rpc_url,
    #     coordinator_address=coordinator_address,
    # )
    print("Deploying smart contracts, private key: ", private_key, "rpc_url: ", rpc_url)
    deploy_smart_contracts(sender=private_key, rpc_url=rpc_url, coordinator_address=coordinator_address)
