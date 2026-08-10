from api.services.rag_pipeline import RAGPipeline


class IntegrationService:

    def __init__(self, pipeline: RAGPipeline | None = None) -> None:
        self.pipeline = pipeline or RAGPipeline()

    def process_query(self, query: str) -> dict:
        return self.pipeline.run(query)
