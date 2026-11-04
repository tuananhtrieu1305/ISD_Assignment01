"""Inspect installed SDK signatures without network calls or key output."""
import inspect,json
from google import genai
from google.genai import types

client=genai.Client(api_key='not-a-real-key')
print(json.dumps({'interactions':hasattr(client,'interactions'),'create_signature':str(inspect.signature(client.interactions.create)),
                  'retry_options':hasattr(types,'HttpRetryOptions')}))
client.close()
