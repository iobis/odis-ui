class RecordNotFoundError(Exception):
    def __init__(self, record_id: str) -> None:
        self.record_id = record_id
        super().__init__(record_id)
