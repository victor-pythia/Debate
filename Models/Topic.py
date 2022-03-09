class Topic:
    def __init__(self, id=None, post_date=None, text="", creator=None):
        self.id = id
        self.text = text
        self.creator = creator
        self.post_date = post_date