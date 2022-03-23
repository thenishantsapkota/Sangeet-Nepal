from tortoise import fields
from tortoise.models import Model


class SavedPlaylists(Model):
    id = fields.IntField(pk=True)
    member_id = fields.BigIntField()
    playlist_url = fields.TextField()
    playlist_name = fields.TextField()

    class Meta:
        table = "saved_playlists"
        table_description = "This table stores saved user playlists"
