async def query_classification(state, llm):
    # easy or non-nested complex or nested complex
    return "easy"

async def easy_query(state, llm):
    return "easy query"

async def non_nested_complex_query(state, llm):
    return "non-nested complex query"

async def nested_complex_query(state, llm):
    return "nested complex query"

async def query_validation(state):
    return {'isvalid' : 'True',
            'error': None}

async def self_correction(state, llm):
    error = state['validation']['error']
    return f"Correcting the query based on the error: {error}"