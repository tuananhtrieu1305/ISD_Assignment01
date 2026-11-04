# GENERATED from notebooks/01_Data_KB_RAG.ipynb; source SHA256 e66fdae9d414f4450b83ae1c19a4ee9e6cd184103ece1c1eeeed2c05b67aeb5f
# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.
"""Group schema inheritance, with medical source metadata and verified claims."""

from pydantic import BaseModel,ConfigDict,Field,field_validator

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

    @field_validator('id',mode='before')
    @classmethod
    def canonical_id(cls,value):
        # IDs are labels, not medical values. Do not coerce bool/float/objects.
        return str(value) if type(value) is int else value
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

