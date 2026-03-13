from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from src.aGraph.nodes import (query_classification, 
                              easy_query, 
                              non_nested_complex_query, 
                              nested_complex_query, 
                              query_validation,
                              self_correction)

# State of the graph
class State(TypedDict):
    # query in text from the user
    input: str
    # schema of the sql
    schema: dict # dict with table names as keys and list of column names as values
    # query output from the graph
    output: str 
    # classification of the query: easy, non_nested_complex, nested_complex
    classification: str
    # validation result of the query
    validation: dict # dict with 'isvalid' (True/False) and 'error' (str or None)

def get_graph(state: State, llm) -> StateGraph[State]:
    graph = StateGraph(State)
    
    # Classifier/Router
    async def query_classification_async (state: State): return await query_classification(state, llm) 
    async def classifier(state: State):
        nxt_step = state['classification']
        if nxt_step not in ['easy', 'non_nested_complex', 'nested_complex']:
            raise ValueError(f"Invalid classification: {nxt_step}")
        return nxt_step
    
    # Query functions
    async def easy_query_async (state: State): return await easy_query(state, llm)
    async def non_nested_complex_query_async (state: State): return await non_nested_complex_query(state, llm)
    async def nested_complex_query_async (state: State): return await nested_complex_query(state, llm)

    # Self correction functions
    async def query_validation_async (state: State): return await query_validation(state)
    async def validation(state: State):
        validation_result = state['validation']['isvalid']
        if validation_result not in ['True', 'False']:
            raise ValueError(f"Invalid validation result: {validation_result}")
        return validation_result        
    async def self_correction_async (state: State): return await self_correction(state, llm)

    # Nodes
    graph.add_node('classifier', query_classification_async)
    graph.add_node('easy', easy_query_async)
    graph.add_node('non_nested_complex', non_nested_complex_query_async)
    graph.add_node('nested_complex', nested_complex_query_async)
    graph.add_node('validation', query_validation_async)
    graph.add_node('self_correction', self_correction_async)

    # Edges
    graph.add_edge(START, 'classifier')
    graph.add_conditional_edges('classifier', classifier,
    {
        'easy': 'easy',
        'non_nested_complex': 'non_nested_complex',
        'nested_complex': 'nested_complex'
    })  
    graph.add_edge('easy', 'validation')
    graph.add_edge('non_nested_complex', 'validation')
    graph.add_edge('nested_complex', 'validation')

    graph.add_conditional_edges('validation', validation, 
    {
        'True': END,
        'False': 'self_correction'
    })

    graph.add_edge('self_correction', 'validation')

    return graph.compile()