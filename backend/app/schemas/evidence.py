from pydantic import BaseModel


class PipelineRunRequest(BaseModel):
    case_id: str
    evidence_file_paths: list[str]


class PipelineRunResponse(BaseModel):
    task_id: str
    status: str


class RetrievalQuery(BaseModel):
    case_id: str
    question: str
