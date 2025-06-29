# Generated by Django 5.2.1 on 2025-06-15 08:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("jobs", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="proposalattachment",
            name="description",
            field=models.TextField(
                blank=True, help_text="Optional description for the file"
            ),
        ),
        migrations.AlterField(
            model_name="proposalattachment",
            name="file",
            field=models.FileField(
                help_text="Upload a file related to your proposal",
                max_length=255,
                upload_to="proposal_attachments/%Y/%m/%d/",
            ),
        ),
        migrations.AlterField(
            model_name="proposalattachment",
            name="file_size",
            field=models.PositiveIntegerField(
                default=0, help_text="File size in bytes"
            ),
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("verb", models.CharField(max_length=255)),
                (
                    "target_object_id",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("emailed", models.BooleanField(default=False)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="actor_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "target_content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="target_obj",
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["recipient", "read_at"],
                        name="jobs_notifi_recipie_bc2925_idx",
                    ),
                    models.Index(
                        fields=["created_at"], name="jobs_notifi_created_877f84_idx"
                    ),
                ],
            },
        ),
    ]
