from css_mux import CSSProvider

# List of models supported by each provider
models = {
    CSSProvider.OPENAI: [
        {"id": "gpt-4o", "name": "GPT-4o", "parameters": None},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "parameters": None},
        {"id": "chatgpt-4o-latest", "name": "ChatGPT-4o Latest", "parameters": None},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "parameters": None},
        {
            "id": "gpt-4-turbo-preview",
            "name": "GPT-4 Turbo Preview",
            "parameters": None,
        },
        {"id": "gpt-4", "name": "GPT-4", "parameters": None},
        {"id": "openai:gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "parameters": None},
        {
            "id": "text-embedding-3-small",
            "name": "Text Embedding 3 Small",
            "parameters": None,
        },
        {
            "id": "text-embedding-3-large",
            "name": "Text Embedding 3 Large",
            "parameters": None,
        },
        {
            "id": "text-embedding-ada-002",
            "name": "Text Embedding Ada 002",
            "parameters": None,
        },
    ],
    CSSProvider.PERPLEXITYAI: [
        {
            "id": "llama-3-sonar-small-32k-chat",
            "name": "Llama 3 Sonar Small 32k Chat",
            "parameters": "8B",
        },
        {
            "id": "llama-3-sonar-small-32k-online",
            "name": "Llama 3 Sonar Small 32k Online",
            "parameters": "8B",
        },
        {
            "id": "llama-3-sonar-large-32k-chat",
            "name": "Llama 3 Sonar Large 32k Chat",
            "parameters": "70B",
        },
        {
            "id": "llama-3-sonar-large-32k-online",
            "name": "Llama 3 Sonar Large 32k Online",
            "parameters": "70B",
        },
        {
            "id": "llama-3-8b-instruct",
            "name": "Llama 3 8B Instruct",
            "parameters": "8B",
        },
        {
            "id": "llama-3-70b-instruct",
            "name": "Llama 3 70B Instruct",
            "parameters": "70B",
        },
        {
            "id": "mixtral-8x7b-instruct",
            "name": "Mixtral 8x7B Instruct",
            "parameters": "8x7B",
        },
    ],
    CSSProvider.GOOSEAI: [
        {"id": "gpt-neo-20b", "name": "GPT NeoX 20B", "parameters": "20B"},
        {"id": "fairseqNone25m", "name": "Fairseq 125M", "parameters": "125M"},
        {"id": "fairseqNone-3b", "name": "Fairseq 1.3B", "parameters": "1.3B"},
        {"id": "fairseq-2-7b", "name": "Fairseq 2.7B", "parameters": "2.7B"},
        {"id": "fairseq-6b-7b", "name": "Fairseq 6.7B", "parameters": "6.7B"},
        {"id": "fairseqNone3b", "name": "Fairseq 13B", "parameters": "13B"},
        {"id": "gpt-j-6b", "name": "GPT-J 6B", "parameters": "6B"},
        {"id": "gpt-neoNone25m", "name": "GPT-Neo 125M", "parameters": "125M"},
        {"id": "gpt-neoNone-3b", "name": "GPT-Neo 1.3B", "parameters": "1.3B"},
        {"id": "gpt-neo-2-7b", "name": "GPT-Neo 2.7B", "parameters": "2.7B"},
    ],
}
