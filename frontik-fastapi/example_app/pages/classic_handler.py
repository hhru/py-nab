from frontik.handler import AwaitablePageHandler

from example_app.routes import example_route
from ffapi.dep import DepBuilder
from ffapi.handler import current_handler, get_current_handler


class TestHandler(AwaitablePageHandler):
    async def get_page(self):
        future = await DepBuilder(example_route).override(get_current_handler, self).build()

        await future
        self.json.put({"status": "ok"})
