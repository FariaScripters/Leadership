# Placeholder for MongoDB connection
class MongoDB:
    async def initialize(self): pass
    async def shutdown(self): pass
    @property
    def client(self):
        class Dummy:
            def __getitem__(self, key): return None
        return Dummy()

def get_mongodb():
    return MongoDB()
