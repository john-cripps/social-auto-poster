from social_autoposter.sheets import SheetClient


def test_sheet_rows_are_parsed_without_building_google_client():
    class Values:
        def get(self, **kwargs):
            return self
        def execute(self):
            return {"values": [["id", "stream", "body", "image_url", "link", "platforms", "publish_at", "status", "posted_at", "error"], ["1", "agency", "Hello", "", "", "bluesky", "", "queued", "", ""]]}

    class Sheets:
        def values(self):
            return Values()

    posts = SheetClient("sheet", "Posts", {}, service=type("Service", (), {"spreadsheets": lambda self: Sheets()})()).read_posts()
    assert posts[0].content.body == "Hello"
    assert posts[0].platforms == ["bluesky"]
