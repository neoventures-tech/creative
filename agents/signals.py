import os
import re

from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from agents.models import GeneratedImage, Message


@receiver(post_save, sender=Message)
def link_to_message_to_image(sender, instance, created, **kwargs):
    if created:

        last_image_with_no_message = (
            GeneratedImage.objects.filter(
                conversation=instance.conversation,
                message__isnull=True,
            ).last()
        )

        if last_image_with_no_message:
            last_image_with_no_message.message = instance
            last_image_with_no_message.save()
