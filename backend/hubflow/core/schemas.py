from ninja import Schema


class BackupOut(Schema):
    filename: str
    size: int
