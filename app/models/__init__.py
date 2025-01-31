# Import models in the correct order to avoid circular dependencies
from app.models.user import User
from app.models.classroom import Classroom, ClassroomMember
from app.models.classroom_request import ClassroomRequest
from app.models.forum import ForumPost, ForumComment
from app.models.notification import Notification
from app.models.file_attachment import FileAttachment

__all__ = [
    'User',
    'Classroom',
    'ClassroomMember',
    'ClassroomRequest',
    'ForumPost',
    'ForumComment',
    'Notification',
    'FileAttachment'
]

# This file intentionally left empty to make the directory a Python package
