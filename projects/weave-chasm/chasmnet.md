# Running Chasm's Weave on Infernet

In this tutorial we are going to integrate [Chasm's Weave](https://weave.Chasm.net/) into infernet. We will:

1. Obtain an API key from Chasm
2. Configure the `chasmnet` service, build & deploy it with Infernet
3. Make a web-2 request by directly prompting the [Weave service](./container)
4. Make a web-3 request by integrating a sample [`PromptsGPT.sol`](./contracts/src/PromptsGPT.sol) smart contract. This
contract will make a request to Infernet with their prompt, and receive the result of the request.

## Install Pre-requisites

For this tutorial you'll need to have the following installed.

1. [Docker](https://docs.docker.com/engine/install/)
2. [Foundry](https://book.getfoundry.sh/getting-started/installation)

### Get an API key from Chasm

First, you'll need to get an API key from Chasm. You can do this by making
an [Chasm](https://Chasm.net/) account.
After signing in, head over to [their platform](https://weave.Chasm.net/) to
make an API key.

> [!NOTE]
> You will need a paid account to use the Weave API.

### Ensure `docker` & `foundry` exist

To check for `docker`, run the following command in your terminal:
```bash copy
docker --version
# Docker version 25.0.2, build 29cf629 (example output)
```

You'll also need to ensure that docker-compose exists in your terminal:
```bash copy
which docker-compose
# /usr/local/bin/docker-compose (example output)
```

To check for `foundry`, run the following command in your terminal:
```bash copy
forge --version
# forge 0.2.0 (551bcb5 2024-02-28T07:40:42.782478000Z) (example output)
```

### Clone the starter repository
Just like our other examples, we're going to clone this repository.
All of the code and instructions for this tutorial can be found in the
[`projects/weave-chasm`](https://github.com/ritual-net/infernet-container-starter/tree/main/projects/weave-chasm)
directory of the repository.

```bash copy
# Clone locally
git clone --recurse-submodules https://github.com/ritual-net/infernet-container-starter
# Navigate to the repository
cd infernet-container-starter
```

### Configure the `weave-chasm` container

#### Configure API key in `config.json`
This is where we'll use the API key we obtained from Chasm.

```bash
cd projects/weave-chasm/container
cp config.sample.json config.json
```

In the `containers` field, you will see the following. Replace `your-Chasm-key` with your Chasm API key.

```json
"containers": [
    {
        // etc. etc.
        "env": {
            "CHASMNET_API_KEY": "your-Chasm-key" // replace with your Chasm API key
        }
    }
],
```

### Build the `weave-chasm` container

First, navigate back to the root of the repository. Then simply run the following command to build the `gpt4`
container:

```bash copy
cd ../../..
make build-container project=weave-chasm
```

### Deploy infernet node locally

Much like our [hello world](../hello-world/hello-world.md) project, deploying the infernet node is as
simple as running:

```bash copy
make deploy-container project=weave-chasm
```

## Making a Web2 Request

From here, you can directly make a request to the infernet node:
```bash
# prompts with no input
curl -X POST http://127.0.0.1:4000/api/jobs -H "Content-Type: application/json" -d '{"containers":["weave-chasm"],"data":{"body":{"endpoint":"prompts","endpoint_id":"9395","input":{}}}}'
# {"id":"7a4ff474-e9ca-48b5-acb3-7c441e60a638"}
```c


```bash
# prompts with input
curl -X POST http://127.0.0.1:4000/api/jobs -H "Content-Type: application/json" -d '{"containers":["weave-chasm"],"data":{"body":{"endpoint":"prompts","endpoint_id":"9793","input":{"food": "apples"}}}}'
# {"id":"5eb3f76c-4da2-4b33-a4ca-9201171956be"}
```c


If you have `jq` installed, you can pipe the output of the last command to a file:

```bash copy
curl -X POST http://127.0.0.1:4000/api/jobs -H "Content-Type: application/json" -d '{"containers":["weave-chasm"],"data":{"body":{"endpoint":"prompts","endpoint_id":"9395","input":{}}}}' | jq -r ".id" > last-job.uuid
```

You can then check the status of the job by running:

```bash copy
curl -X GET http://127.0.0.1:4000/api/jobs\?id\=7a4ff474-e9ca-48b5-acb3-7c441e60a638
# response [{"id":"5eb3f76c-4da2-4b33-a4ca-9201171956be","result":{"container":"weave-chasm","output":{"message":"Food is any substance consumed to provide nutritional support for the body. It is usually of plant or animal origin and contains essential nutrients such as carbohydrates, fats, proteins, vitamins, and minerals. Food serves as fuel for the body, providing energy and supporting various bodily functions. Additionally, food can also be enjoyed for its taste, texture, and cultural significance."}},"status":"success"}]
```

And if you have `jq` installed and piped the last output to a file, you can instead run:

```bash
curl -X GET "http://127.0.0.1:4000/api/jobs?id=$(cat last-request.uuid)" | jq .
# returns something like:
[
    {
        "id": "5eb3f76c-4da2-4b33-a4ca-9201171956be",
        "result": {
            "container": "weave-chasm",
            "output": {
                "message": "Food is any substance consumed to provide nutritional support for the body. It is usually of plant or animal origin and contains essential nutrients such as carbohydrates, fats, proteins, vitamins, and minerals. Food serves as fuel for the body, providing energy and supporting various bodily functions. Additionally, food can also be enjoyed for its taste, texture, and cultural significance."
            }
        },
        "status": "success"
    }
]
```

## Making a Web3 Request

Now let's bring this service onchain! First we'll have to deploy the contracts.
The [contracts](contracts)
directory contains a simple foundry project with a simple contract called `PromptsGpt`.
This contract exposes a single
function `function promptGPT(string calldata prompt)`. Using this function you'll be
able to make an infernet request.

**Anvil Logs**: First, it's useful to look at the logs of the anvil node to see what's
going on. In a new terminal, run `docker logs -f anvil-node`.
If there's installation issues, run the following in the `infernet-container-starter` folder to ensure the needed libraries are installed.
```bash
cd projects/weave-chasm/contracts && forge install --no-commit foundry-rs/forge-std && forge install --no-commit ritual-net/infernet-sdk && cd ../../../
```

**Deploying the contracts**: In another terminal, run the following command:

```bash
make deploy-contracts project=weave-chasm
```

### Calling the contract

Now, let's call the contract. So far everything's been identical to
the [hello world](projects/hello-world/README.mdllo-world/README.md) project. The only
difference here is that calling the contract requires an input. We'll pass that input in
using an env var named
`prompt`:

```bash copy
make call-contract project=weave-chasm prompt="Can shrimps actually fry rice"
```

On your anvil logs, you should see something like this:

```bash
eth_sendRawTransaction

_____  _____ _______ _    _         _
|  __ \|_   _|__   __| |  | |  /\   | |
| |__) | | |    | |  | |  | | /  \  | |
|  _  /  | |    | |  | |  | |/ /\ \ | |
| | \ \ _| |_   | |  | |__| / ____ \| |____
|_|  \_\_____|  |_|   \____/_/    \_\______|


subscription Id 1
interval 1
redundancy 1
node 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
output: {'output': 'Yes, shrimps can be used to make fried rice. Fried rice is a versatile dish that can be made with various ingredients, including shrimp. Shrimp fried rice is a popular dish in many cuisines, especially in Asian cuisine.'}

    Transaction: 0x9bcab42cf7348953eaf107ca0ca539cb27f3843c1bb08cf359484c71fcf44d2b
    Gas used: 93726

    Block Number: 3
    Block Hash: 0x1cc39d03bb1d69ea7f32db85d2ee684071e28b6d6de9eab6f57e011e11a7ed08
    Block Time: "Fri, 26 Jan 2024 02:30:37 +0000"
```

beautiful, isn't it? 🥰
