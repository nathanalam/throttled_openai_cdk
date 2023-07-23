# Throttled ML API CDK Stack

This creates an API to call with a pre-existing Open API key that throttles requests and
maintains a limit to calls to stay under a certian token limit per day. This allows easy integration
of your OpenAPI usage into your other development stacks without the fear of excessive charges ramping up.

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template

## Development

Requires use of Docker to bundle the lambda code.

Instructions for installing Docker: https://docs.docker.com/get-docker/

You can also optionally set up a python virtual environment and install the relevant python libraries for development:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r resources/lambda_src/throttled_open_ai/requirements.txt
```

Before deploying, you must set the `OPEN_API_KEY` environment variable:
```
OPEN_API_KEY=<insert_key>
npm run cdk deploy
```
