import os
from dotenv import load_dotenv
current_file_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_file_dir, '..', '..', '.env.development')
load_dotenv(dotenv_path)

import json
import re
import time
import logging
import markdown
import datetime
import asyncio
from groq import Groq
import hashlib
from anthropic import Anthropic
import openai
from app import app
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LLM:
    CACHE_DIR = 'llm_cache'

    @classmethod
    def name_session(cls,chat):
        prompt = f"Given this chat, give a 2-4 word summary, nothing else:\n{chat}"
        return cls.call(prompt,{"model":"llama3-8b-8192"})

    @classmethod
    def _generate_cache_key(cls, service, model, messages):
        # Create a string representation of service, model, and messages
        cache_data = json.dumps({
            'service': service,
            'model': model,
            'messages': messages
        }, sort_keys=True)

        # Generate a hash of the cache data
        return hashlib.md5(cache_data.encode()).hexdigest()

    @classmethod
    def _get_from_cache(cls, cache_key):
        cache_file = os.path.join(cls.CACHE_DIR, f"{cache_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None

    @classmethod
    def _save_to_cache(cls, cache_key, data):
        if not os.path.exists(cls.CACHE_DIR):
            os.makedirs(cls.CACHE_DIR)
        cache_file = os.path.join(cls.CACHE_DIR, f"{cache_key}.json")
        with open(cache_file, 'w') as f:
            json.dump(data, f)

    @classmethod
    def get_default_model(cls,service):
        defaults = {
                'claude': "claude-3-opus-20240229",
                'openai': "gpt-4-0125-preview",
                'blitzkong': "mistral-7b-instruct-v0.1",
                'groq': "llama-3.1-70b-versatile",
                'gemini': "gemini-1.5-flash"
                }
        return defaults.get(service, "unknown")

    @classmethod
    def call(cls, prompt_or_messages, opts={}):
        retry = opts.get("retry", 2)
        service = opts.get("service", "groq")
        use_cache = opts.get("use_cache", False)

        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        elif isinstance(prompt_or_messages, list):
            messages = prompt_or_messages
            logger.info(f"Prompt: {prompt_or_messages[0]['content'][:50]}")
        else:
            raise ValueError("prompt_or_messages should be either a string or a list of messages")

        logger.info(f"Prompt: {messages[:50]}")

        # Generate a cache key based on the service, model, and prompt
        model = opts.get("model", cls.get_default_model(service))
        cache_key = cls._generate_cache_key(service, model, messages)

        # Try to get the response from cache
        if use_cache:
            cached_response = cls._get_from_cache(cache_key)
            if cached_response:
                logger.info("Cache hit. Returning cached response.")
                return cached_response

        for attempt in range(retry + 1):
            try:
                start_time = time.time()

                if service == 'claude':
                    client = Anthropic(api_key=ANTHROPIC_API_KEY)
                    chat_completion = client.messages.create(
                            model=model,
                            messages=messages,
                            max_tokens=4096,
                            temperature=0
                            )
                    response = chat_completion.content[0].text
                elif service == 'openai':
                    client = openai.OpenAI(api_key=os.getenv("OPEN_API_KEY"))
                    chat_completion = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=0,
                            **({"response_format": {"type": "json_object"}} if opts.get("json",False) else {})
                            )
                    response = chat_completion.choices[0].message.content
                elif service == 'blitzkong':
                    client = openai.OpenAI(api_key='NONE', base_url=f"{BLITZKONG_HOST}/v1")
                    chat_completion = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=0
                            )
                    response = chat_completion.choices[0].message.content
                elif service == 'groq':
                    client = Groq(api_key=os.getenv("GROQ_KEY"))
                    chat_completion = client.chat.completions.create(
                            messages=messages, model=model, temperature=0)
                    response = chat_completion.choices[0].message.content
                elif service == 'gemini':
                    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                    genaimodel = genai.GenerativeModel(model)
                    chat = genaimodel.start_chat(history=[])
                    response = chat.send_message(messages[-1]['content']).text
                else:
                    raise ValueError(f"Unsupported service: {service}")

                end_time = time.time()
                runtime = end_time - start_time
                logger.info(f"Runtime: {runtime:.2f} seconds")

                if opts.get("json", False):
                    json_response = cls.to_json(response)
                    if json_response is None:
                        raise ValueError("Failed to convert response to JSON")
                    else:
                        # Cache the JSON response
                        if use_cache:
                            cls._save_to_cache(cache_key, json_response)
                        if isinstance(json_response, list) and len(json_response) == 1:
                            json_response = json_response[0] 
                        return json_response
                else:
                    # Cache the text response
                    if use_cache:
                        cls._save_to_cache(cache_key, response)
                    return response
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt == retry:
                    raise e
                else:
                    logger.info(f"Retrying... ({attempt + 1}/{retry})")

    @classmethod
    async def call_async(cls, prompt, opts={}):
        # Implement async version of the call method
        return await asyncio.to_thread(cls.call, prompt, opts)

    @classmethod
    def template(cls,template_name,opts={}):
        app_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(app_dir, 'templates', 'general', template_name)
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        return cls.call(template_content, opts)

    @classmethod
    def to_domain(cls,string):
        # select name,importance,searchVolume,directUrl,url from merchants order by importance, searchVolume desc limit 1000
        prompt = f'''return the best matching root domain to answer the question given the query, dont include www.
only return the url such as:
amazon.com 
nike.com

query:
{string}'''

        output = LLM.call(prompt)
        return output

    @classmethod
    def to_category(cls,string):
        # TODO isaac give us a list of all categories
        output = LLM.call(f"extract the general product category (ie shoes or pants) for the given string, only return the category. Always return a category that is the closest match.:\n\n {string}")
        return output

    @classmethod
    def to_product(cls,string):
        output = LLM.call(f"extract the product from the given string, only return the product name:\n\n {string}")
        print(f"PRODUCT:{output}")
        return output

    @classmethod
    def to_json(cls,output,can_raise=False):
        def log_unparsed_json(data):
            if not os.path.exists('bad_json'):
                os.makedirs('bad_json')
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bad_json/{timestamp}.txt"
            with open(filename, 'w') as file:
                file.write(data)
        try:
            json_data = json.loads(output)
            return json_data
        except json.JSONDecodeError:
            pass
        regex = r"```(.*?)```"
        matches = re.findall(regex, output, re.DOTALL)
        if matches:
            try:
                json_data = json.loads(matches[0])
                return json_data
            except json.JSONDecodeError:
                pass

        json_objects = []
        json_pattern = r"\{.*?\}"
        for match in re.findall(json_pattern, output, re.DOTALL):
            try:
                json_data = json.loads(match)
                json_objects.append(json_data)
            except json.JSONDecodeError:
                # Skip invalid JSON objects
                pass
        if json_objects:
            return json_objects

        json_regex = re.compile(r'\{.*\}|\[.*\]', re.DOTALL)
        match = json_regex.search(output)

        if match:
            json_str = match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        #TODO finally try with llm and return something
        print(f"problem with JSON\n{output}")
        log_unparsed_json(output)
        return None

    @classmethod
    def to_html(cls,string):
        try:
            # Try to convert using markdown library
            return markdown.markdown(string)
        except Exception:
            # If markdown conversion fails, use LLM
            prompt = f"Take the following text and convert it to HTML for people to click on links, return only the HTML and nothing else:\n\n{string}"
            print(f"TO_HTML\n{prompt}")
            return LLM.call(prompt)
