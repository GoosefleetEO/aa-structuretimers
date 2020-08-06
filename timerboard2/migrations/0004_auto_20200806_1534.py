# Generated by Django 2.2.13 on 2020-08-06 15:34

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ("timerboard2", "0003_auto_20200806_1115"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notificationrule",
            name="require_timer_types",
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True,
                choices=[
                    ("NO", "Unspecified"),
                    ("AR", "Armor"),
                    ("HL", "Hull"),
                    ("FI", "Final"),
                    ("AN", "Anchoring"),
                    ("UA", "Unanchoring"),
                    ("MM", "Moon Mining"),
                ],
                help_text="Timer must have one of the given timer types or leave blank to match any.",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="timer",
            name="timer_type",
            field=models.CharField(
                choices=[
                    ("NO", "Unspecified"),
                    ("AR", "Armor"),
                    ("HL", "Hull"),
                    ("FI", "Final"),
                    ("AN", "Anchoring"),
                    ("UA", "Unanchoring"),
                    ("MM", "Moon Mining"),
                ],
                default="NO",
                max_length=2,
                verbose_name="timer type",
            ),
        ),
    ]