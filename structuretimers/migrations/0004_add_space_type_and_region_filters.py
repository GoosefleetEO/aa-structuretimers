# Generated by Django 4.0.3 on 2022-04-19 18:58

import multiselectfield.db.fields

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("eveuniverse", "0007_evetype_description"),
        ("eveonline", "0015_factions"),
        ("structuretimers", "0003_add_preliminary_timers"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationrule",
            name="exclude_regions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Timer must NOT be created within one of the given regions",
                related_name="+",
                to="eveuniverse.everegion",
            ),
        ),
        migrations.AddField(
            model_name="notificationrule",
            name="exclude_space_types",
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True,
                choices=[
                    ("HS", "highsec"),
                    ("LS", "lowsec"),
                    ("NS", "nullsec"),
                    ("WS", "wh space"),
                ],
                help_text="Space Type must NOT be one of the selected",
                max_length=11,
            ),
        ),
        migrations.AddField(
            model_name="notificationrule",
            name="require_regions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Timer must be created within one of the given regions or leave blank to match any.",
                related_name="+",
                to="eveuniverse.everegion",
            ),
        ),
        migrations.AddField(
            model_name="notificationrule",
            name="require_space_types",
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True,
                choices=[
                    ("HS", "highsec"),
                    ("LS", "lowsec"),
                    ("NS", "nullsec"),
                    ("WS", "wh space"),
                ],
                help_text="Space type must be one of the selected or leave blank to match any.",
                max_length=11,
            ),
        ),
        migrations.AlterField(
            model_name="notificationrule",
            name="exclude_alliances",
            field=models.ManyToManyField(
                blank=True,
                help_text="Timer must NOT be created by one of the given alliances",
                related_name="+",
                to="eveonline.eveallianceinfo",
            ),
        ),
        migrations.AlterField(
            model_name="notificationrule",
            name="require_alliances",
            field=models.ManyToManyField(
                blank=True,
                help_text="Timer must be created by one of the given alliances or leave blank to match any.",
                related_name="+",
                to="eveonline.eveallianceinfo",
            ),
        ),
        migrations.AlterField(
            model_name="notificationrule",
            name="require_corporations",
            field=models.ManyToManyField(
                blank=True,
                help_text="Timer must be created by one of the given corporations or leave blank to match any.",
                related_name="+",
                to="eveonline.evecorporationinfo",
            ),
        ),
    ]
