import binaryninja

from .comments_viewer import view_comments

binaryninja.PluginCommand.register(
    "Comments Viewer",
    "View all comments",
    view_comments,
)
