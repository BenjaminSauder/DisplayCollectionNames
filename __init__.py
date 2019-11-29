import bpy
import bgl
import blf

from bpy.app.handlers import persistent
from time import perf_counter

bl_info = {
    "name": "Display Collection Names",
    "description": "Prints the collection names of the selected objects into the 3D View.",
    "author": "Benajmin Sauder",
    "version": (1, 0),
    "blender": (2, 81, 0),
    "location": "View3D",
    "category": "3D View"
}


class Updater():
    '''
    This just encapsulates all relevant data, and a few helper methods to extract placement and texts.
    '''

    collections_text = ""
    active_object = None

    last_update = 0
    x = 0
    y = 0

    def update_collection_names(self):
        selected_objects = bpy.context.selected_objects

        if len(selected_objects) == 0:
            self.collections_text = ""
            return False

        collection_names = set()
        for obj in selected_objects:
            collections = [c.name_full for c in obj.users_collection]
            collection_names.update(collections)

        self.collections_text = " | ".join(collection_names)

        return True

    def find_region(self, width, height):
        ''' 
        As I know no good way to get the correct context into the draw call back,
        I do this viewport size comparison - its a bit weak, lets hope its good enough...
        '''
        context = bpy.context
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            if (width == region.width and
                                    height == region.height):
                                return region, area
        return None, None

    def update_placement(self, do_update):
        if not do_update and perf_counter() > (self.last_update + 0.25):
            return

        viewport_info = bgl.Buffer(bgl.GL_INT, 4)
        bgl.glGetIntegerv(bgl.GL_VIEWPORT, viewport_info)

        width = viewport_info[2]
        height = viewport_info[3]

        x_offset = 0
        y_offset = 0

        region, area = self.find_region(width, height)
        if region:
            for region in area.regions:
                if region.type == 'TOOLS':
                    x_offset = region.width
                if region.type == 'HEADER':
                    y_offset = region.height
                if region.type == 'TOOL_HEADER':
                    y_offset = region.height

        self.x = x_offset + 18
        self.y = height - y_offset - 60
        self.last_update = perf_counter()

    def draw(self, dummy):
        if not bpy.context.space_data.overlay.show_text:
            return

        do_update = self.update_collection_names()
        self.update_placement(do_update)

        font_id = 0

        bgl.glEnable(bgl.GL_BLEND)
        blf.enable(font_id, blf.SHADOW)

        blf.color(font_id, 1.0, 1.0, 1.0, 1)
        blf.size(font_id, 11, 72)
        blf.position(0, self.x, self.y, 0)

        blf.draw(font_id, self.collections_text)

        blf.disable(font_id, blf.SHADOW)
        bgl.glDisable(bgl.GL_BLEND)


updater = Updater()


def register():
    args = (updater,)
    updater.draw_handler = bpy.types.SpaceView3D.draw_handler_add(
        updater.draw, args, 'WINDOW', 'POST_PIXEL')


def unregister():
    if updater.draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(
            updater.draw_handler, 'WINDOW')
    updater.draw_handler = None


if __name__ == "__main__":
    register()
