# GENERATED from notebooks/01_Data_KB_RAG.ipynb; source SHA256 6f04e14fc770a34a38301f3048e511b1f06a3aa42ede996ff05ff02bc88b7b4b
# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.
"""Group schema inheritance, with medical source metadata and verified claims."""

from pydantic import BaseModel,ConfigDict,Field

class APIModel(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)

class MetaData(APIModel):
    document_id:str
    title:str
    source:str|None=None
    section:str|None=None
    subsection:str|None=None
    source_refs:list[dict]=Field(default_factory=list)

class Chunk(APIModel):
    chunk_id:str
    content:str
    chunk_index:int=Field(ge=0)
    metadata:MetaData

class SearchResult(Chunk):
    score:float
    dense_rank:int|None=None
    sparse_rank:int|None=None
    kg_rank:int|None=None
    graph_assertion_ids:list[str]=Field(default_factory=list)

class RankedResult(SearchResult):
    rerank_score:float
    original_rank:int=Field(ge=1)

class SourceResponse(Chunk):
    score:float|None=None
    score_type:str

class Claim(APIModel):
    id:str
    text_vi:str
    citation_chunk_ids:list[str]=Field(default_factory=list)

class Draft(APIModel):
    answer_vi:str=Field(min_length=1)
    claims:list[Claim]=Field(default_factory=list)
    limitations:list[str]=Field(default_factory=list)

class ChatResponse(APIModel):
    answer:str
    sources:list[SourceResponse]

class CompareRequest(APIModel):
    question:str=Field(min_length=1,max_length=4096)
    profile:dict|None=None
    mode:str='knowledge'

