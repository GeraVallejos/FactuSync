from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("enterprise_documents", "0004_tenant_operation_mode_tenantmembership"),
    ]

    operations = [
        migrations.AddField(
            model_name="taxserviceprofile",
            name="certificate_password_encrypted",
            field=models.TextField(blank=True),
        ),
    ]
