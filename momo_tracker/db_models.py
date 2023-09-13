from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.CharField(pk=True, max_length=33)
    line_notify_token = fields.CharField(max_length=255, null=True)
    items: fields.ManyToManyRelation["Item"] = fields.ManyToManyField(
        "models.Item", related_name="users", through="user_item"
    )


class Item(Model):
    id = fields.CharField(pk=True, max_length=255)
    name = fields.CharField(max_length=255)
    users: fields.ManyToManyRelation[User]


class PromotionItem(Model):
    id = fields.CharField(pk=True, max_length=255)
    url = fields.CharField(max_length=255)
    original_price = fields.IntField()
    discount_price = fields.IntField()
    discount_rate = fields.FloatField()
    name = fields.CharField(max_length=255)
    brand_name = fields.CharField(max_length=255)
    remain_count = fields.IntField()
