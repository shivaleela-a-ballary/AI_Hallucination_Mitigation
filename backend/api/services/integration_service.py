from api.services.rag_pipeline import RAGPipeline


class IntegrationService:

    def __init__(self):

        self.pipeline = RAGPipeline()

    def process_query(self, query: str):

        return self.pipeline.run(query)